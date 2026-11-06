"""Proteção das views por perfil (usa a política central de apps/contas/escopo.py)."""

from functools import wraps

from django.contrib.auth.decorators import login_required

from apps.contas import escopo


def perfil_exigido(*perfis):
    """Anônimo vai para o login; quem não tem um dos perfis recebe 403."""

    def decorador(view):
        @login_required
        @wraps(view)
        def protegida(request, *args, **kwargs):
            escopo.exigir_perfil(request.user, *perfis)
            return view(request, *args, **kwargs)

        return protegida

    return decorador
