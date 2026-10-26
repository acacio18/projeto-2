"""Verificação de saúde da aplicação."""

import subprocess  # nosec B404: usado só para consultar o Tesseract, com comando fixo

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


def _banco_responde():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return False
    return True


def _tesseract_tem_portugues():
    try:
        # Executável vem da configuração do servidor; sem shell e sem entrada do usuário.
        resultado = subprocess.run(  # nosec B603
            [settings.TESSERACT_CMD, "--list-langs"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    # Conforme a versão, o Tesseract lista os idiomas no stdout ou no stderr.
    linhas = (resultado.stdout + resultado.stderr).splitlines()
    return "por" in {linha.strip() for linha in linhas}


@require_GET
def healthz(request):
    verificacoes = {
        "banco": _banco_responde(),
        "tesseract_por": _tesseract_tem_portugues(),
    }
    saudavel = all(verificacoes.values())
    return JsonResponse(
        {"status": "ok" if saudavel else "falha", "verificacoes": verificacoes},
        status=200 if saudavel else 503,
    )
