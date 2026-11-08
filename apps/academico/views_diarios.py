"""Diários: lista, detalhe com as versões das notas, cadastro e vínculo de turma e professor.

Toda consulta parte de escopo.diarios_visiveis; alterar exige gerenciar o curso do diário; confirmar,
descartar e escolher a versão vigente exige ser o professor responsável ou gerenciar o curso.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.academico import servicos
from apps.academico.formularios import FiltroDiarios, FormularioDiario
from apps.academico.models import Diario
from apps.contas import escopo
from apps.importacao import servicos as versoes
from apps.importacao.models import Importacao, StatusImportacao
from apps.notas import consultas

POR_PAGINA = 25


def _diario_visivel(request, pk):
    return escopo.obter_visivel(
        escopo.diarios_visiveis(request.user).select_related("curso", "disciplina", "turma", "professor"), pk
    )


def _exigir_gerencia(request, diario):
    if not escopo.pode_gerenciar_curso(request.user, diario.curso):
        raise PermissionDenied


@login_required
def lista(request):
    vigente = Importacao.objects.filter(diario=OuterRef("pk"), vigente=True).values("numero_versao")[:1]
    diarios = (
        escopo.diarios_visiveis(request.user)
        .select_related("curso", "disciplina", "turma", "professor")
        .annotate(
            versao_vigente=Subquery(vigente),
            aguardando=Count(
                "importacoes", filter=Q(importacoes__status=StatusImportacao.AGUARDANDO_CONFIRMACAO)
            ),
        )
        .order_by("-ano_letivo", "disciplina__nome", "codigo")
    )
    filtro = FiltroDiarios(request.GET or None)
    if filtro.is_valid():
        dados = filtro.cleaned_data
        if dados["q"]:
            diarios = diarios.filter(
                Q(codigo__icontains=dados["q"])
                | Q(disciplina__nome__icontains=dados["q"])
                | Q(disciplina__codigo__icontains=dados["q"])
            )
        if dados["ano"]:
            diarios = diarios.filter(ano_letivo=dados["ano"])
        situacao = dados["situacao"]
        if situacao == "com_notas":
            diarios = diarios.filter(versao_vigente__isnull=False)
        elif situacao == "sem_notas":
            diarios = diarios.filter(versao_vigente__isnull=True)
        elif situacao == "aguardando":
            diarios = diarios.filter(aguardando__gt=0)
        elif situacao == "sem_turma":
            diarios = diarios.filter(turma__isnull=True)
    pagina = Paginator(diarios, POR_PAGINA).get_page(request.GET.get("pagina"))
    parametros = request.GET.copy()
    parametros.pop("pagina", None)
    contexto = {
        "filtro": filtro,
        "pagina": pagina,
        "parametros": parametros.urlencode(),
        "pode_cadastrar": escopo.cursos_gerenciaveis(request.user).exists(),
    }
    return render(request, "academico/diarios/lista.html", contexto)


@login_required
def detalhe(request, pk):
    diario = _diario_visivel(request, pk)
    confirmadas = list(consultas.versoes(diario).select_related("confirmada_por", "enviada_por"))
    pendentes = list(consultas.pendentes(diario).select_related("enviada_por"))
    selecionada = None
    if "importacao" in request.GET:
        selecionada = next(
            (i for i in pendentes + confirmadas if str(i.pk) == request.GET["importacao"]), None
        )
        if selecionada is None:
            raise Http404
    else:
        selecionada = next((i for i in confirmadas if i.vigente), None) or (
            pendentes[0] if pendentes else None
        )
    contexto = {
        "diario": diario,
        "confirmadas": confirmadas,
        "pendentes": pendentes,
        "selecionada": selecionada,
        "linhas": consultas.linhas_da_versao(selecionada) if selecionada else [],
        "pode_cuidar": versoes.pode_cuidar_do_diario(request.user, diario),
        "pode_editar": escopo.pode_gerenciar_curso(request.user, diario.curso),
    }
    return render(request, "academico/diarios/detalhe.html", contexto)


@login_required
@require_http_methods(["GET", "POST"])
def novo(request):
    if not escopo.cursos_gerenciaveis(request.user).exists():
        raise PermissionDenied
    form = FormularioDiario(request.POST or None, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            diario = servicos.salvar_diario(por=request.user, dados=form.cleaned_data, request=request)
        except ValidationError as erro:
            form.add_error(None, " ".join(erro.messages))
        else:
            messages.success(request, f"Diário {diario.codigo} cadastrado.")
            return redirect("diarios:detalhe", pk=diario.pk)
    return render(
        request, "academico/formulario.html", _contexto_formulario(form, "Novo diário", "diarios:lista")
    )


@login_required
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    diario = _diario_visivel(request, pk)
    _exigir_gerencia(request, diario)
    form = FormularioDiario(request.POST or None, instance=diario, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            servicos.salvar_diario(
                por=request.user, diario=Diario.objects.get(pk=pk), dados=form.cleaned_data, request=request
            )
        except ValidationError as erro:
            form.add_error(None, " ".join(erro.messages))
        else:
            messages.success(request, "Alterações salvas.")
            return redirect("diarios:detalhe", pk=pk)
    contexto = _contexto_formulario(
        form, f"Diário {Diario.objects.get(pk=pk).codigo}", "diarios:detalhe", pk=pk
    )
    contexto["excluir_url"] = "diarios:excluir"
    contexto["objeto"] = diario
    return render(request, "academico/formulario.html", contexto)


@login_required
@require_http_methods(["GET", "POST"])
def excluir(request, pk):
    diario = _diario_visivel(request, pk)
    _exigir_gerencia(request, diario)
    if request.method == "POST":
        try:
            servicos.excluir_diario(por=request.user, diario=diario, request=request)
        except ValidationError as erro:
            messages.error(request, " ".join(erro.messages))
            return redirect("diarios:detalhe", pk=pk)
        messages.success(request, f"Diário {diario.codigo} excluído.")
        return redirect("diarios:lista")
    return render(
        request,
        "academico/excluir.html",
        {"objeto": diario, "descricao": f"o diário {diario}", "voltar": ("diarios:detalhe", pk)},
    )


def _importacao_do_diario(request, pk, importacao_pk):
    diario = _diario_visivel(request, pk)
    return get_object_or_404(Importacao, pk=importacao_pk, diario=diario)


def _acao_de_versao(request, pk, importacao_pk, operacao, sucesso):
    importacao = _importacao_do_diario(request, pk, importacao_pk)
    try:
        resultado = operacao(por=request.user, importacao=importacao, request=request)
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
        return redirect("diarios:detalhe", pk=pk)
    messages.success(request, sucesso(resultado))
    return redirect("diarios:detalhe", pk=pk)


@login_required
@require_POST
def confirmar_versao(request, pk, importacao_pk):
    return _acao_de_versao(
        request,
        pk,
        importacao_pk,
        versoes.confirmar_versao,
        lambda v: f"Notas confirmadas como versão {v.numero_versao}, agora vigente.",
    )


@login_required
@require_POST
def descartar_versao(request, pk, importacao_pk):
    return _acao_de_versao(
        request,
        pk,
        importacao_pk,
        versoes.descartar_versao,
        lambda v: "Importação descartada. Nada foi alterado.",
    )


@login_required
@require_POST
def tornar_vigente(request, pk, importacao_pk):
    return _acao_de_versao(
        request,
        pk,
        importacao_pk,
        versoes.definir_versao_vigente,
        lambda v: f"A versão {v.numero_versao} passou a ser a vigente.",
    )


def _contexto_formulario(form, titulo, voltar, pk=None):
    return {"form": form, "titulo": titulo, "voltar": (voltar, pk) if pk else (voltar, None)}
