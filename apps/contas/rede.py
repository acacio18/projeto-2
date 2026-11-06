"""Dados de rede da requisição, usados pela auditoria e pelo bloqueio de login (django-axes).

O IP vem só do REMOTE_ADDR. Cabeçalhos como X-Forwarded-For podem ser forjados pelo cliente; eles só
serão considerados na E10, quando houver um proxy reverso confiável configurado.
"""

import ipaddress


def ip_do_cliente(request) -> str | None:
    endereco = request.META.get("REMOTE_ADDR")
    try:
        return str(ipaddress.ip_address(endereco))
    except (TypeError, ValueError):
        return None


def agente_do_cliente(request) -> str:
    return request.META.get("HTTP_USER_AGENT", "")[:300]
