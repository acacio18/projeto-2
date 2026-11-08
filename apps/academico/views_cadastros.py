"""Cadastros de cursos (Administrador), turmas e disciplinas (Administrador ou Coordenador do curso).

Listas: cada um vê o que está no seu escopo. Alterar exige gerenciar o curso; fora do escopo é 404.
"""

from collections.abc import Callable
from dataclasses import dataclass

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.academico import servicos
from apps.academico.formularios import (
    FiltroCadastros,
    FormularioCoordenador,
    FormularioCurso,
    FormularioDisciplina,
    FormularioTurma,
)
from apps.academico.models import Curso, Disciplina, Turma
from apps.contas import escopo

POR_PAGINA = 25


@login_required
def inicio(request):
    usuario = request.user
    contexto = {
        "total_cursos": escopo.cursos_visiveis(usuario).count(),
        "total_turmas": escopo.turmas_visiveis(usuario).count(),
        "total_disciplinas": escopo.disciplinas_visiveis(usuario).count(),
        "gerencia": escopo.cursos_gerenciaveis(usuario).exists(),
    }
    return render(request, "academico/cadastros/inicio.html", contexto)


# --- Cursos ------------------------------------------------------------------------------------


@login_required
def cursos(request):
    lista = escopo.cursos_visiveis(request.user).annotate(
        n_turmas=Count("turmas", distinct=True),
        n_disciplinas=Count("disciplinas", distinct=True),
        n_diarios=Count("diarios", distinct=True),
    )
    contexto = {
        "cursos": lista.order_by("nome"),
        "pode_cadastrar": escopo.pode_cadastrar_cursos(request.user),
    }
    return render(request, "academico/cadastros/cursos.html", contexto)


@login_required
def curso_detalhe(request, pk):
    curso = escopo.obter_visivel(escopo.cursos_visiveis(request.user), pk)
    gerencia = escopo.pode_gerenciar_curso(request.user, curso)
    admin = escopo.pode_cadastrar_cursos(request.user)
    contexto = {
        "curso": curso,
        "gerencia": gerencia,
        "admin": admin,
        "coordenadores": curso.coordenadores.order_by("nome"),
        "professores": escopo.professores_do_curso(curso) if gerencia else None,
        "turmas": escopo.turmas_visiveis(request.user).filter(curso=curso).count(),
        "disciplinas": escopo.disciplinas_visiveis(request.user).filter(curso=curso).count(),
        "diarios": escopo.diarios_visiveis(request.user).filter(curso=curso).count(),
        "form_coordenador": FormularioCoordenador(curso=curso) if admin else None,
    }
    return render(request, "academico/cadastros/curso_detalhe.html", contexto)


def _exigir_admin(request):
    if not escopo.pode_cadastrar_cursos(request.user):
        raise PermissionDenied


@login_required
@require_http_methods(["GET", "POST"])
def curso_novo(request):
    _exigir_admin(request)
    form = FormularioCurso(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            curso = servicos.salvar_curso(por=request.user, dados=form.cleaned_data, request=request)
        except ValidationError as erro:
            form.add_error(None, " ".join(erro.messages))
        else:
            messages.success(request, f"Curso {curso.nome} cadastrado.")
            return redirect("cadastros:curso", pk=curso.pk)
    return render(
        request,
        "academico/formulario.html",
        {"form": form, "titulo": "Novo curso", "voltar": ("cadastros:cursos", None)},
    )


@login_required
@require_http_methods(["GET", "POST"])
def curso_editar(request, pk):
    _exigir_admin(request)
    curso = get_object_or_404(Curso, pk=pk)
    form = FormularioCurso(request.POST or None, instance=curso)
    if request.method == "POST" and form.is_valid():
        try:
            servicos.salvar_curso(
                por=request.user, curso=Curso.objects.get(pk=pk), dados=form.cleaned_data, request=request
            )
        except ValidationError as erro:
            form.add_error(None, " ".join(erro.messages))
        else:
            messages.success(request, "Alterações salvas.")
            return redirect("cadastros:curso", pk=pk)
    contexto = {
        "form": form,
        "titulo": f"Editar curso {Curso.objects.get(pk=pk).codigo}",
        "voltar": ("cadastros:curso", pk),
        "excluir_url": "cadastros:curso_excluir",
        "objeto": curso,
    }
    return render(request, "academico/formulario.html", contexto)


@login_required
@require_http_methods(["GET", "POST"])
def curso_excluir(request, pk):
    _exigir_admin(request)
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == "POST":
        try:
            servicos.excluir_curso(por=request.user, curso=curso, request=request)
        except ValidationError as erro:
            messages.error(request, " ".join(erro.messages))
            return redirect("cadastros:curso", pk=pk)
        messages.success(request, f"Curso {curso.nome} excluído.")
        return redirect("cadastros:cursos")
    return render(
        request,
        "academico/excluir.html",
        {"objeto": curso, "descricao": f"o curso {curso}", "voltar": ("cadastros:curso", pk)},
    )


@login_required
@require_POST
def coordenador_vincular(request, pk):
    _exigir_admin(request)
    curso = get_object_or_404(Curso, pk=pk)
    form = FormularioCoordenador(request.POST, curso=curso)
    if form.is_valid():
        usuario = form.cleaned_data["usuario"]
        servicos.vincular_coordenador(por=request.user, curso=curso, usuario=usuario, request=request)
        messages.success(request, f"{usuario.nome} agora coordena {curso.nome}.")
    else:
        messages.error(request, "Escolha um coordenador válido.")
    return redirect("cadastros:curso", pk=pk)


@login_required
@require_POST
def coordenador_desvincular(request, pk, usuario_pk):
    _exigir_admin(request)
    curso = get_object_or_404(Curso, pk=pk)
    usuario = get_object_or_404(get_user_model(), pk=usuario_pk)
    servicos.desvincular_coordenador(por=request.user, curso=curso, usuario=usuario, request=request)
    messages.success(request, f"{usuario.nome} não coordena mais {curso.nome}.")
    return redirect("cadastros:curso", pk=pk)


# --- Turmas e disciplinas (mesmo fluxo) --------------------------------------------------------


@dataclass(frozen=True)
class Cadastro:
    nome: str  # "turma"
    plural: str  # "turmas"
    modelo: type
    formulario: type
    visiveis: Callable
    salvar: Callable
    excluir: Callable
    busca: tuple[str, ...]
    ordem: tuple[str, ...]


CADASTROS = {
    "turmas": Cadastro(
        "turma",
        "turmas",
        Turma,
        FormularioTurma,
        escopo.turmas_visiveis,
        lambda por, obj, dados, request: servicos.salvar_turma(
            por=por, turma=obj, dados=dados, request=request
        ),
        lambda por, obj, request: servicos.excluir_turma(por=por, turma=obj, request=request),
        ("identificador__icontains",),
        ("-ano_letivo", "curso__nome", "identificador"),
    ),
    "disciplinas": Cadastro(
        "disciplina",
        "disciplinas",
        Disciplina,
        FormularioDisciplina,
        escopo.disciplinas_visiveis,
        lambda por, obj, dados, request: servicos.salvar_disciplina(
            por=por, disciplina=obj, dados=dados, request=request
        ),
        lambda por, obj, request: servicos.excluir_disciplina(por=por, disciplina=obj, request=request),
        ("nome__icontains", "codigo__icontains"),
        ("curso__nome", "nome"),
    ),
}


def _objeto(request, cadastro, pk, para_alterar=False):
    objeto = escopo.obter_visivel(cadastro.visiveis(request.user).select_related("curso"), pk)
    if para_alterar and not escopo.pode_gerenciar_curso(request.user, objeto.curso):
        raise PermissionDenied
    return objeto


@login_required
def lista(request, tipo):
    cadastro = CADASTROS[tipo]
    objetos = cadastro.visiveis(request.user).select_related("curso").annotate(n_diarios=Count("diarios"))
    filtro = FiltroCadastros(request.GET or None, usuario=request.user)
    if filtro.is_valid():
        if filtro.cleaned_data["q"]:
            busca = Q()
            for campo in cadastro.busca:
                busca |= Q(**{campo: filtro.cleaned_data["q"]})
            objetos = objetos.filter(busca)
        if filtro.cleaned_data["curso"]:
            objetos = objetos.filter(curso=filtro.cleaned_data["curso"])
    pagina = Paginator(objetos.order_by(*cadastro.ordem), POR_PAGINA).get_page(request.GET.get("pagina"))
    parametros = request.GET.copy()
    parametros.pop("pagina", None)
    gerenciaveis = set(escopo.cursos_gerenciaveis(request.user).values_list("pk", flat=True))
    contexto = {
        "cadastro": cadastro,
        "tipo": tipo,
        "filtro": filtro,
        "pagina": pagina,
        "parametros": parametros.urlencode(),
        "gerenciaveis": gerenciaveis,
        "pode_cadastrar": bool(gerenciaveis),
    }
    return render(request, f"academico/cadastros/{tipo}.html", contexto)


@login_required
@require_http_methods(["GET", "POST"])
def novo(request, tipo):
    cadastro = CADASTROS[tipo]
    if not escopo.cursos_gerenciaveis(request.user).exists():
        raise PermissionDenied
    inicial = {"curso": request.GET.get("curso")} if request.GET.get("curso") else None
    form = cadastro.formulario(request.POST or None, initial=inicial, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            objeto = cadastro.salvar(request.user, None, form.cleaned_data, request)
        except ValidationError as erro:
            form.add_error(None, " ".join(erro.messages))
        else:
            messages.success(request, f"{cadastro.nome.capitalize()} {objeto} cadastrada.")
            return redirect(f"cadastros:{tipo}")
    contexto = {"form": form, "titulo": f"Nova {cadastro.nome}", "voltar": (f"cadastros:{tipo}", None)}
    return render(request, "academico/formulario.html", contexto)


@login_required
@require_http_methods(["GET", "POST"])
def editar(request, tipo, pk):
    cadastro = CADASTROS[tipo]
    objeto = _objeto(request, cadastro, pk, para_alterar=True)
    form = cadastro.formulario(request.POST or None, instance=objeto, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            cadastro.salvar(request.user, cadastro.modelo.objects.get(pk=pk), form.cleaned_data, request)
        except ValidationError as erro:
            form.add_error(None, " ".join(erro.messages))
        else:
            messages.success(request, "Alterações salvas.")
            return redirect(f"cadastros:{tipo}")
    contexto = {
        "form": form,
        "titulo": f"Editar {cadastro.nome} {cadastro.modelo.objects.get(pk=pk)}",
        "voltar": (f"cadastros:{tipo}", None),
        "excluir_url": f"cadastros:{cadastro.nome}_excluir",
        "objeto": objeto,
    }
    return render(request, "academico/formulario.html", contexto)


@login_required
@require_http_methods(["GET", "POST"])
def excluir(request, tipo, pk):
    cadastro = CADASTROS[tipo]
    objeto = _objeto(request, cadastro, pk, para_alterar=True)
    if request.method == "POST":
        try:
            cadastro.excluir(request.user, objeto, request)
        except ValidationError as erro:
            messages.error(request, " ".join(erro.messages))
            return redirect(f"cadastros:{cadastro.nome}_editar", pk=pk)
        messages.success(request, f"{cadastro.nome.capitalize()} {objeto} excluída.")
        return redirect(f"cadastros:{tipo}")
    contexto = {
        "objeto": objeto,
        "descricao": f"a {cadastro.nome} {objeto}",
        "voltar": (f"cadastros:{cadastro.nome}_editar", pk),
    }
    return render(request, "academico/excluir.html", contexto)
