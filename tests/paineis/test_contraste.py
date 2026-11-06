"""Contraste WCAG dos tokens de cor do static/css/app.css, nos temas claro e escuro.

Lê os tokens direto do CSS: se alguém mudar uma cor e quebrar o contraste, este teste falha.
"""

import re
from pathlib import Path

import pytest

CSS = (Path(__file__).resolve().parents[2] / "static" / "css" / "app.css").read_text(encoding="utf-8")

# (texto, fundo) que precisam de 4,5:1 (texto comum, WCAG 1.4.3)
PARES_TEXTO = [
    ("--cor-texto", "--cor-fundo"),
    ("--cor-texto", "--cor-superficie"),
    ("--cor-texto", "--cor-superficie-alternativa"),
    ("--cor-texto", "--cor-erro-fundo"),
    ("--cor-texto", "--cor-sucesso-fundo"),
    ("--cor-texto", "--cor-aviso-fundo"),
    ("--cor-texto", "--cor-info-fundo"),
    ("--cor-texto-secundario", "--cor-fundo"),
    ("--cor-texto-secundario", "--cor-superficie"),
    ("--cor-texto-secundario", "--cor-superficie-alternativa"),
    ("--cor-texto-secundario", "--cor-neutro-fundo"),
    ("--cor-link", "--cor-fundo"),
    ("--cor-link", "--cor-superficie"),
    ("--cor-sobre-primaria", "--cor-primaria"),
    ("--cor-sobre-primaria", "--cor-primaria-hover"),
    ("--cor-erro", "--cor-fundo"),
    ("--cor-erro", "--cor-superficie"),
    ("--cor-sucesso", "--cor-sucesso-fundo"),
    ("--cor-aviso", "--cor-aviso-fundo"),
    ("--cor-texto", "--cor-neutro-fundo"),
]
# (componente, fundo) que precisam de 3:1 (contornos de campos e foco, WCAG 1.4.11)
PARES_COMPONENTE = [
    ("--cor-borda-campo", "--cor-superficie"),
    ("--cor-marca", "--cor-superficie"),
    ("--cor-marca", "--cor-fundo"),
    ("--cor-primaria", "--cor-fundo"),
]
BOTAO_PERIGO = [("#ffffff", "--vermelho-500"), ("#ffffff", "--vermelho-700")]


def _bloco(seletor_regex: str) -> dict[str, str]:
    corpo = re.search(seletor_regex + r"\s*\{(.*?)\n\s*\}", CSS, re.DOTALL).group(1)
    return dict(re.findall(r"(--[\w-]+):\s*([^;]+);", corpo))


CLARO = _bloco(r"\n:root")
ESCURO_SISTEMA = _bloco(r':root:not\(\[data-tema="claro"\]\)')
ESCURO_ESCOLHIDO = _bloco(r':root\[data-tema="escuro"\]')
ESCURO = {**CLARO, **ESCURO_ESCOLHIDO}


def _resolver(tokens: dict[str, str], valor: str) -> str:
    """Segue a cadeia de tokens (--a: var(--b); --b: #hex) até chegar na cor."""
    if valor.startswith("--"):
        valor = tokens[valor].strip()
    while valor.startswith("var("):
        valor = tokens[re.fullmatch(r"var\((--[\w-]+)\)", valor).group(1)].strip()
    return valor


def _luminancia(hexa: str) -> float:
    canais = [int(hexa[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lineares = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * lineares[0] + 0.7152 * lineares[1] + 0.0722 * lineares[2]


def contraste(a: str, b: str) -> float:
    claro, escuro = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def test_as_duas_copias_do_tema_escuro_sao_iguais():
    assert ESCURO_SISTEMA == ESCURO_ESCOLHIDO


def test_cores_oficiais_do_if_estao_nos_tokens():
    assert CLARO["--verde-500"] == "#2f9e41"
    assert CLARO["--vermelho-500"] == "#cd191e"


@pytest.mark.parametrize("tema", ["claro", "escuro"])
@pytest.mark.parametrize(("frente", "fundo"), PARES_TEXTO)
def test_texto_tem_contraste_minimo_de_4_5(tema, frente, fundo):
    tokens = CLARO if tema == "claro" else ESCURO
    razao = contraste(_resolver(tokens, frente), _resolver(tokens, fundo))
    assert razao >= 4.5, f"{frente} sobre {fundo} no tema {tema}: {razao:.2f}"


@pytest.mark.parametrize("tema", ["claro", "escuro"])
@pytest.mark.parametrize(("frente", "fundo"), PARES_COMPONENTE)
def test_componentes_tem_contraste_minimo_de_3(tema, frente, fundo):
    tokens = CLARO if tema == "claro" else ESCURO
    razao = contraste(_resolver(tokens, frente), _resolver(tokens, fundo))
    assert razao >= 3, f"{frente} sobre {fundo} no tema {tema}: {razao:.2f}"


@pytest.mark.parametrize(("frente", "fundo"), BOTAO_PERIGO)
def test_botao_de_perigo(frente, fundo):
    assert contraste(frente, _resolver(CLARO, fundo)) >= 4.5
