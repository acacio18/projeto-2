"""Casos de uso do cadastro de usuários (ID 15). As telas só chamam estas funções.

Regras:
- só o Administrador cria, altera, desativa e reativa usuários;
- usuários nunca são apagados, só desativados (a auditoria aponta para eles);
- ninguém desativa a si mesmo, e o sistema nunca fica sem um Administrador ativo;
- toda operação gera um evento de auditoria com o que mudou.
"""

from axes.utils import reset as zerar_tentativas
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.auditoria.models import TipoEvento
from apps.auditoria.registro import registrar
from apps.contas import escopo
from apps.contas.models import Perfil

CAMPOS_EDITAVEIS = ("nome", "email", "perfil")


def _outros_admins_ativos(alvo) -> bool:
    modelo = get_user_model()
    return modelo.objects.filter(perfil=Perfil.ADMIN, is_active=True).exclude(pk=alvo.pk).exists()


@transaction.atomic
def criar_usuario(*, por, nome, email, perfil, request=None):
    """Cria o usuário sem senha utilizável: ele define a própria senha pelo convite."""
    escopo.exigir_perfil(por, Perfil.ADMIN)
    modelo = get_user_model()
    usuario = modelo(nome=nome.strip(), email=email, perfil=perfil)
    usuario.set_unusable_password()
    usuario.full_clean()
    usuario.save()
    registrar(TipoEvento.USUARIO_CRIADO, request=request, usuario=por, objeto=usuario, perfil=usuario.perfil)
    return usuario


@transaction.atomic
def alterar_usuario(*, por, alvo, nome, email, perfil, request=None):
    escopo.exigir_perfil(por, Perfil.ADMIN)
    alvo = escopo.obter_usuario_visivel(por, alvo.pk)
    if (
        alvo.perfil == Perfil.ADMIN
        and perfil != Perfil.ADMIN
        and alvo.is_active
        and not _outros_admins_ativos(alvo)
    ):
        raise ValidationError("O sistema precisa de pelo menos um administrador ativo.", code="ultimo_admin")
    antes = {campo: getattr(alvo, campo) for campo in CAMPOS_EDITAVEIS}
    alvo.nome, alvo.email, alvo.perfil = nome.strip(), email, perfil
    alvo.full_clean()
    depois = {campo: getattr(alvo, campo) for campo in CAMPOS_EDITAVEIS}
    mudancas = {
        c: {"antes": antes[c], "depois": depois[c]} for c in CAMPOS_EDITAVEIS if antes[c] != depois[c]
    }
    if not mudancas:
        return alvo
    alvo.save()
    registrar(TipoEvento.USUARIO_ALTERADO, request=request, usuario=por, objeto=alvo, mudancas=mudancas)
    return alvo


@transaction.atomic
def desativar_usuario(*, por, alvo, request=None):
    escopo.exigir_perfil(por, Perfil.ADMIN)
    alvo = escopo.obter_usuario_visivel(por, alvo.pk)
    # Quem desativa é um administrador ativo e não pode desativar a si mesmo; por isso o sistema
    # nunca fica sem administrador por esta operação.
    if alvo.pk == por.pk:
        raise ValidationError("Você não pode desativar a sua própria conta.", code="desativar_a_si_mesmo")
    if not alvo.is_active:
        return alvo
    alvo.is_active = False
    alvo.save(update_fields=["is_active", "atualizado_em"])
    registrar(TipoEvento.USUARIO_DESATIVADO, request=request, usuario=por, objeto=alvo)
    return alvo


def link_para_definir_senha(usuario, request) -> str:
    """Link de uso único (vale até a senha mudar ou o prazo PASSWORD_RESET_TIMEOUT acabar)."""
    caminho = reverse(
        "contas:definir_senha",
        kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(usuario.pk)),
            "token": default_token_generator.make_token(usuario),
        },
    )
    return request.build_absolute_uri(caminho)


def enviar_convite(*, por, alvo, request):
    """Envia por e-mail o link para o usuário definir a própria senha (o administrador nunca a vê)."""
    escopo.exigir_perfil(por, Perfil.ADMIN)
    alvo = escopo.obter_usuario_visivel(por, alvo.pk)
    if not alvo.is_active:
        raise ValidationError("Reative o usuário antes de enviar o convite.", code="inativo")
    if alvo.has_usable_password():
        raise ValidationError(
            "Este usuário já definiu a senha. Se esqueceu, ele pode usar “Esqueci minha senha”.",
            code="senha_ja_definida",
        )
    contexto = {
        "usuario": alvo,
        "link": link_para_definir_senha(alvo, request),
        "validade_horas": settings.PASSWORD_RESET_TIMEOUT // 3600,
    }
    assunto = render_to_string("contas/emails/convite_assunto.txt", contexto).strip()
    corpo = render_to_string("contas/emails/convite.txt", contexto)
    send_mail(assunto, corpo, None, [alvo.email])
    registrar(TipoEvento.CONVITE_ENVIADO, request=request, usuario=por, objeto=alvo)


def desbloquear_login(*, por, alvo, request=None):
    """Zera as tentativas de login erradas (fim antecipado do bloqueio do django-axes)."""
    escopo.exigir_perfil(por, Perfil.ADMIN)
    alvo = escopo.obter_usuario_visivel(por, alvo.pk)
    zerar_tentativas(username=alvo.email)
    registrar(TipoEvento.LOGIN_DESBLOQUEADO, request=request, usuario=por, objeto=alvo)


@transaction.atomic
def reativar_usuario(*, por, alvo, request=None):
    escopo.exigir_perfil(por, Perfil.ADMIN)
    alvo = escopo.obter_usuario_visivel(por, alvo.pk)
    if alvo.is_active:
        return alvo
    alvo.is_active = True
    alvo.save(update_fields=["is_active", "atualizado_em"])
    registrar(TipoEvento.USUARIO_REATIVADO, request=request, usuario=por, objeto=alvo)
    return alvo
