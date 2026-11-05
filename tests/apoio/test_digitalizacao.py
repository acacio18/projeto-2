"""Confere as versões digitalizadas (só imagem) do boletim de exemplo, usadas nos testes de OCR."""

import math

import pdfplumber
import pytest

from tests.apoio import digitalizacao
from tests.apoio.boletins import BOLETIM_EXEMPLO
from tests.apoio.digitalizacao import PONTOS_POR_POLEGADA, VARIANTES


@pytest.fixture(scope="module")
def tamanho_das_paginas_originais() -> list[tuple[float, float]]:
    """Largura e altura de cada página do PDF original, em pontos."""
    with pdfplumber.open(BOLETIM_EXEMPLO) as pdf:
        return [(pagina.width, pagina.height) for pagina in pdf.pages]


def _pixels(pontos: float, dpi: int) -> float:
    return pontos * dpi / PONTOS_POR_POLEGADA


@pytest.mark.parametrize("nome", sorted(VARIANTES))
def test_so_tem_imagem_sem_camada_de_texto(boletim_digitalizado, nome):
    with pdfplumber.open(boletim_digitalizado(nome)) as pdf:
        assert len(pdf.pages) == 2
        for pagina in pdf.pages:
            assert pagina.chars == []
            assert len(pagina.images) == 1


@pytest.mark.parametrize(
    ("nome", "girada"), [("300dpi", False), ("150dpi", False), ("300dpi_girado90", True)]
)
def test_resolucao_e_orientacao(boletim_digitalizado, tamanho_das_paginas_originais, nome, girada):
    dpi = VARIANTES[nome].dpi
    with pdfplumber.open(boletim_digitalizado(nome)) as pdf:
        for pagina, (largura, altura) in zip(pdf.pages, tamanho_das_paginas_originais, strict=True):
            largura_px, altura_px = pagina.images[0]["srcsize"]
            if girada:
                largura_px, altura_px = altura_px, largura_px
            assert largura_px == pytest.approx(_pixels(largura, dpi), abs=2)
            assert altura_px == pytest.approx(_pixels(altura, dpi), abs=2)


def test_inclinada_ocupa_o_retangulo_da_pagina_girada(boletim_digitalizado, tamanho_das_paginas_originais):
    variante = VARIANTES["300dpi_inclinado"]
    angulo = math.radians(variante.rotacao_graus)
    with pdfplumber.open(boletim_digitalizado("300dpi_inclinado")) as pdf:
        for pagina, (largura, altura) in zip(pdf.pages, tamanho_das_paginas_originais, strict=True):
            w, h = _pixels(largura, variante.dpi), _pixels(altura, variante.dpi)
            largura_px, altura_px = pagina.images[0]["srcsize"]
            assert largura_px == pytest.approx(w * math.cos(angulo) + h * math.sin(angulo), abs=3)
            assert altura_px == pytest.approx(w * math.sin(angulo) + h * math.cos(angulo), abs=3)


def test_geracao_e_deterministica_e_o_ruido_depende_da_semente():
    variante = VARIANTES["300dpi_inclinado"]
    primeira = digitalizacao.impressao_digital(digitalizacao.rasterizar(BOLETIM_EXEMPLO, variante))
    segunda = digitalizacao.impressao_digital(digitalizacao.rasterizar(BOLETIM_EXEMPLO, variante))
    assert primeira == segunda

    outra_semente = digitalizacao.Variante(
        variante.descricao, variante.dpi, variante.rotacao_graus, variante.ruido_desvio, variante.semente + 1
    )
    assert (
        digitalizacao.impressao_digital(digitalizacao.rasterizar(BOLETIM_EXEMPLO, outra_semente)) != primeira
    )


def test_linha_de_comando_gera_a_variante_pedida(tmp_path, capsys):
    assert digitalizacao.main(["--saida", str(tmp_path), "--variante", "150dpi"]) == 0
    gerado = tmp_path / "exemplo_boletins.150dpi.pdf"
    assert gerado.is_file()
    assert [p.name for p in tmp_path.iterdir()] == [gerado.name]
    assert "150dpi" in capsys.readouterr().out
