"""Verificação de saúde da aplicação."""

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.ops import saude


@require_GET
def healthz(request):
    verificacoes = saude.verificar()
    saudavel = all(verificacoes.values())
    return JsonResponse(
        {"status": "ok" if saudavel else "falha", "verificacoes": verificacoes},
        status=200 if saudavel else 503,
    )
