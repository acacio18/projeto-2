"""Cadastro de usuários (ID 15): só o Administrador. As regras ficam em apps/contas/servicos.py."""

from smtplib import SMTPException

from django.contrib import messages
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.contas import escopo, servicos
from apps.contas.autenticacao import login_bloqueado
from apps.contas.decoradores import perfil_exigido
from apps.contas.formularios import FiltroUsuarios, FormularioUsuario
from apps.contas.models import Perfil

POR_PAGINA = 25


def _mensagens_de_erro(erro: ValidationError) -> str:
    return " ".join(erro.messages)


def _enviar_convite(request, usuario) -> None:
    try:
        servicos.enviar_convite(por=request.user, alvo=usuario, request=request)
    except (SMTPException, OSError):
        messages.warning(
            request,
            f"Não foi possível enviar o e-mail de convite para {usuario.email}. "
            "Confira a configuração de e-mail e use “Reenviar convite”.",
        )
    else:
        messages.success(request, f"Convite enviado para {usuario.email}.")


@perfil_exigido(Perfil.ADMIN)
def lista(request):
    filtro = FiltroUsuarios(request.GET or None)
    usuarios = escopo.usuarios_visiveis(request.user).order_by("nome")
    if filtro.is_valid():
        dados = filtro.cleaned_data
        if dados["q"]:
            usuarios = usuarios.filter(Q(nome__icontains=dados["q"]) | Q(email__icontains=dados["q"]))
        if dados["perfil"]:
            usuarios = usuarios.filter(perfil=dados["perfil"])
        situacao = dados["situacao"]
        if situacao == "ativos":
            usuarios = usuarios.filter(is_active=True)
        elif situacao == "desativados":
            usuarios = usuarios.filter(is_active=False)
        elif situacao == "convite":
            usuarios = usuarios.filter(is_active=True, password__startswith=UNUSABLE_PASSWORD_PREFIX)
    pagina = Paginator(usuarios, POR_PAGINA).get_page(request.GET.get("pagina"))
    parametros = request.GET.copy()
    parametros.pop("pagina", None)
    return render(
        request,
        "contas/usuarios/lista.html",
        {"filtro": filtro, "pagina": pagina, "parametros": parametros.urlencode()},
    )


@perfil_exigido(Perfil.ADMIN)
@require_http_methods(["GET", "POST"])
def novo(request):
    form = FormularioUsuario(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            usuario = servicos.criar_usuario(por=request.user, request=request, **form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, _mensagens_de_erro(erro))
        else:
            messages.success(request, f"Usuário {usuario.nome} cadastrado.")
            _enviar_convite(request, usuario)
            return redirect("usuarios:editar", pk=usuario.pk)
    return render(request, "contas/usuarios/formulario.html", {"form": form, "novo": True})


@perfil_exigido(Perfil.ADMIN)
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    alvo = escopo.obter_usuario_visivel(request.user, pk)
    form = FormularioUsuario(request.POST or None, instance=alvo)
    if request.method == "POST" and form.is_valid():
        try:
            servicos.alterar_usuario(por=request.user, alvo=alvo, request=request, **form.cleaned_data)
        except ValidationError as erro:
            form.add_error(None, _mensagens_de_erro(erro))
        else:
            messages.success(request, "Alterações salvas.")
            return redirect("usuarios:editar", pk=pk)
    alvo = escopo.obter_usuario_visivel(request.user, pk)  # dados salvos, não os do formulário inválido
    contexto = {"form": form, "alvo": alvo, "novo": False, "bloqueado": login_bloqueado(alvo.email)}
    return render(request, "contas/usuarios/formulario.html", contexto)


@perfil_exigido(Perfil.ADMIN)
@require_http_methods(["GET", "POST"])
def desativar(request, pk):
    alvo = escopo.obter_usuario_visivel(request.user, pk)
    if request.method == "POST":
        try:
            servicos.desativar_usuario(por=request.user, alvo=alvo, request=request)
        except ValidationError as erro:
            messages.error(request, _mensagens_de_erro(erro))
        else:
            messages.success(request, f"{alvo.nome} foi desativado e não consegue mais entrar.")
        return redirect("usuarios:editar", pk=pk)
    return render(request, "contas/usuarios/desativar.html", {"alvo": alvo})


@perfil_exigido(Perfil.ADMIN)
@require_POST
def reativar(request, pk):
    alvo = escopo.obter_usuario_visivel(request.user, pk)
    servicos.reativar_usuario(por=request.user, alvo=alvo, request=request)
    messages.success(request, f"{alvo.nome} foi reativado.")
    return redirect("usuarios:editar", pk=pk)


@perfil_exigido(Perfil.ADMIN)
@require_POST
def reenviar_convite(request, pk):
    alvo = escopo.obter_usuario_visivel(request.user, pk)
    try:
        _enviar_convite(request, alvo)
    except ValidationError as erro:
        messages.error(request, _mensagens_de_erro(erro))
    return redirect("usuarios:editar", pk=pk)


@perfil_exigido(Perfil.ADMIN)
@require_POST
def desbloquear(request, pk):
    alvo = escopo.obter_usuario_visivel(request.user, pk)
    servicos.desbloquear_login(por=request.user, alvo=alvo, request=request)
    messages.success(request, f"Login de {alvo.nome} desbloqueado.")
    return redirect("usuarios:editar", pk=pk)
