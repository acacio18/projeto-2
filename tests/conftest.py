"""Fixtures compartilhadas por todos os testes: boletim de exemplo, gabarito e versões digitalizadas."""

from collections.abc import Callable
from pathlib import Path

import pytest

from tests.apoio import boletins, digitalizacao


@pytest.fixture(scope="session")
def boletim_exemplo() -> Path:
    """PDF do boletim de exemplo, com camada de texto (docs/referencias/boletins/)."""
    return boletins.BOLETIM_EXEMPLO


@pytest.fixture
def gabarito_exemplo() -> dict:
    """Valores esperados do boletim de exemplo. Lido a cada teste, então alterá-lo não afeta os outros."""
    return boletins.carregar_gabarito()


@pytest.fixture(scope="session")
def boletim_digitalizado(tmp_path_factory, boletim_exemplo) -> Callable[[str], Path]:
    """Fábrica: boletim_digitalizado("300dpi") devolve o PDF só com imagem, gerado uma vez por sessão.

    As variantes disponíveis estão em tests/apoio/digitalizacao.py (VARIANTES).
    """
    pasta = tmp_path_factory.mktemp("boletins_digitalizados")
    gerados: dict[str, Path] = {}

    def obter(nome_variante: str) -> Path:
        if nome_variante not in gerados:
            destino = pasta / digitalizacao.nome_do_arquivo(boletim_exemplo, nome_variante)
            variante = digitalizacao.VARIANTES[nome_variante]
            gerados[nome_variante] = digitalizacao.gerar(boletim_exemplo, destino, variante)
        return gerados[nome_variante]

    return obter
