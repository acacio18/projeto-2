"""Testes do comando ``manage.py verificar_saude``."""

import io

import pytest
from django.core.management import CommandError, call_command

from apps.ops import saude


def _executar(monkeypatch, resultado):
    monkeypatch.setattr(saude, "verificar", lambda: resultado)
    saida = io.StringIO()
    return saida, lambda: call_command("verificar_saude", stdout=saida)


def test_lista_todas_as_verificacoes_quando_tudo_passa(monkeypatch):
    saida, executar = _executar(monkeypatch, {"banco": True, "tesseract_por": True})

    executar()

    linhas = saida.getvalue().splitlines()
    assert len(linhas) == 2
    assert all(linha.startswith("OK") for linha in linhas)
    assert "Banco de dados" in linhas[0]
    assert "Tesseract" in linhas[1]


def test_falha_com_erro_quando_alguma_verificacao_falha(monkeypatch):
    saida, executar = _executar(monkeypatch, {"banco": False, "tesseract_por": True})

    with pytest.raises(CommandError, match="falha"):
        executar()

    assert saida.getvalue().splitlines()[0].startswith("FALHA")
