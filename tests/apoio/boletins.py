"""Caminhos e carregamento dos boletins de teste e dos seus gabaritos."""

import json
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_FIXTURES = RAIZ_PROJETO / "tests" / "fixtures" / "boletins"

BOLETIM_EXEMPLO = RAIZ_PROJETO / "docs" / "referencias" / "boletins" / "exemplo_boletins.pdf"
GABARITO_EXEMPLO = PASTA_FIXTURES / "exemplo_boletins.gabarito.json"


def carregar_gabarito(caminho: Path = GABARITO_EXEMPLO) -> dict:
    """Lê um gabarito JSON (valores que o leitor de boletins deve extrair do PDF)."""
    return json.loads(caminho.read_text(encoding="utf-8"))


def caminho_do_pdf(gabarito: dict) -> Path:
    """PDF a que o gabarito se refere (o campo "arquivo" é relativo à raiz do projeto)."""
    return RAIZ_PROJETO / gabarito["arquivo"]
