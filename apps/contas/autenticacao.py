"""Apoio à autenticação usado pelo django-axes."""

from axes.models import AccessAttempt
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone


def login_bloqueado(email: str) -> bool:
    """A conta está bloqueada agora por excesso de tentativas erradas?"""
    desde = timezone.now() - settings.AXES_COOLOFF_TIME
    falhas = AccessAttempt.objects.filter(username=email.strip().lower(), attempt_time__gte=desde).aggregate(
        total=Sum("failures_since_start")
    )["total"]
    return (falhas or 0) >= settings.AXES_FAILURE_LIMIT


def email_da_tentativa(request, credentials) -> str | None:
    """E-mail digitado no login, normalizado.

    O bloqueio é por conta: sem normalizar, "Prof@IFPB.edu.br" e "prof@ifpb.edu.br" contariam as
    falhas separadamente e permitiriam o dobro de tentativas.

    As credenciais chegam com a chave "username" (sinal de falha do Django e formulário de login) ou
    "email" (USERNAME_FIELD do modelo, usado por outros caminhos de autenticação). As duas valem: se
    só uma fosse lida, a verificação e o registro das falhas olhariam contas diferentes.
    """
    valor = None
    if credentials:
        valor = credentials.get("username") or credentials.get("email")
    if valor is None and request is not None:
        valor = request.POST.get("username")
    return valor.strip().lower() if isinstance(valor, str) else None
