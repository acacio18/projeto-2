"""Registra na auditoria os eventos de autenticação emitidos pelo Django e pelo django-axes."""

from axes.signals import user_locked_out
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from apps.auditoria.models import TipoEvento
from apps.auditoria.registro import registrar


@receiver(user_logged_in, dispatch_uid="auditoria_login_sucesso")
def _login_sucesso(sender, request, user, **kwargs):
    registrar(TipoEvento.LOGIN_SUCESSO, request=request, usuario=user)


@receiver(user_logged_out, dispatch_uid="auditoria_logout")
def _logout(sender, request, user, **kwargs):
    registrar(TipoEvento.LOGOUT, request=request, usuario=user)


@receiver(user_login_failed, dispatch_uid="auditoria_login_falha")
def _login_falha(sender, credentials, request=None, **kwargs):
    # O Django já troca a senha por asteriscos em `credentials`; guardamos só o e-mail digitado.
    registrar(
        TipoEvento.LOGIN_FALHA,
        request=request,
        email_informado=str(credentials.get("username", "")),
        conta_bloqueada=bool(getattr(request, "axes_locked_out", False)),
    )


@receiver(user_locked_out, dispatch_uid="auditoria_conta_bloqueada")
def _conta_bloqueada(sender, request, username, ip_address, **kwargs):
    registrar(TipoEvento.CONTA_BLOQUEADA, request=request, email_informado=str(username or ""))
