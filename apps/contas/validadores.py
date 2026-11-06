"""Validação do e-mail institucional (domínios configuráveis em CONTAS_DOMINIOS_EMAIL)."""

from django.conf import settings
from django.core.exceptions import ValidationError


def dominios_permitidos() -> list[str]:
    return [dominio.lower().lstrip("@") for dominio in settings.CONTAS_DOMINIOS_EMAIL]


def validar_email_institucional(email: str) -> None:
    """Aceita só e-mails dos domínios institucionais configurados (sem subdomínios)."""
    dominio = email.rsplit("@", 1)[-1].lower() if "@" in email else ""
    permitidos = dominios_permitidos()
    if dominio not in permitidos:
        raise ValidationError(
            "Use o seu e-mail institucional (%(dominios)s).",
            code="email_nao_institucional",
            params={"dominios": ", ".join(f"@{d}" for d in permitidos)},
        )
