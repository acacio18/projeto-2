"""Template tags da interface: ícones SVG (Lucide) embutidos no HTML."""

import re
from functools import cache
from pathlib import Path

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

PASTA_ICONES = Path(__file__).resolve().parent.parent / "icones"
NOME_VALIDO = re.compile(r"^[a-z0-9-]+$")


@cache
def _svg(nome: str) -> str:
    if not NOME_VALIDO.fullmatch(nome):
        raise ValueError(f"Nome de ícone inválido: {nome!r}")
    texto = (PASTA_ICONES / f"{nome}.svg").read_text(encoding="utf-8")
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.DOTALL)  # comentário de licença (está no LICENSE)
    texto = re.sub(r'\s+class="[^"]*"', "", texto, count=1)
    return " ".join(texto.split())


@register.simple_tag
def icone(nome: str, classe: str = "") -> str:
    """{% icone "log-in" %}: ícone decorativo (o texto ao lado ou o aria-label do botão dão o sentido)."""
    classes = escape(f"icone {classe}".strip())
    svg = _svg(nome).replace("<svg ", f'<svg class="{classes}" aria-hidden="true" focusable="false" ', 1)
    return mark_safe(svg)  # nosec B308 B703 # SVG local versionado (conferido sem script) e classe escapada
