"""Casos de uso do cadastro de usuários (ID 15). As telas só chamam estas funções.

Regras:
- só o Administrador cria, altera, desativa e reativa usuários;
- usuários nunca são apagados, só desativados (a auditoria aponta para eles);
- ninguém desativa a si mesmo, e o sistema nunca fica sem um Administrador ativo;
- toda operação gera um evento de auditoria com o que mudou.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

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
