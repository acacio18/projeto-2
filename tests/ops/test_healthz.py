"""Testes do endpoint de verificação de saúde (/healthz)."""

import subprocess

import pytest
from django.db import OperationalError
from django.urls import reverse

from apps.ops import views

SAUDAVEL = {"status": "ok", "verificacoes": {"banco": True, "tesseract_por": True}}


def _simular_tesseract(monkeypatch, stdout="", stderr=""):
    def executar(*args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(views.subprocess, "run", executar)


@pytest.fixture
def tesseract_com_portugues(monkeypatch):
    _simular_tesseract(monkeypatch, stdout='List of available languages in "tessdata/" (3):\neng\nosd\npor\n')


@pytest.mark.django_db
def test_responde_200_quando_banco_e_tesseract_estao_ok(client, tesseract_com_portugues):
    resposta = client.get(reverse("healthz"))

    assert resposta.status_code == 200
    assert resposta.json() == SAUDAVEL


@pytest.mark.django_db
def test_aceita_lista_de_idiomas_no_stderr(client, monkeypatch):
    _simular_tesseract(monkeypatch, stderr="List of available languages (2):\nosd\npor\n")

    resposta = client.get(reverse("healthz"))

    assert resposta.status_code == 200
    assert resposta.json() == SAUDAVEL


@pytest.mark.django_db
def test_responde_503_sem_idioma_portugues(client, monkeypatch):
    _simular_tesseract(monkeypatch, stdout="List of available languages (2):\neng\nosd\n")

    resposta = client.get(reverse("healthz"))

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "falha", "verificacoes": {"banco": True, "tesseract_por": False}}


@pytest.mark.django_db
def test_nao_confunde_idioma_que_apenas_contem_por(client, monkeypatch):
    _simular_tesseract(monkeypatch, stdout="List of available languages (1):\nport_custom\n")

    resposta = client.get(reverse("healthz"))

    assert resposta.json()["verificacoes"]["tesseract_por"] is False


@pytest.mark.django_db
def test_responde_503_quando_executavel_do_tesseract_nao_existe(client, settings, tmp_path):
    settings.TESSERACT_CMD = str(tmp_path / "nao-existe" / "tesseract.exe")

    resposta = client.get(reverse("healthz"))

    assert resposta.status_code == 503
    assert resposta.json()["verificacoes"]["tesseract_por"] is False


@pytest.mark.django_db
def test_responde_503_quando_tesseract_excede_o_tempo(client, monkeypatch):
    def demorar(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="tesseract", timeout=10)

    monkeypatch.setattr(views.subprocess, "run", demorar)

    resposta = client.get(reverse("healthz"))

    assert resposta.status_code == 503
    assert resposta.json()["verificacoes"]["tesseract_por"] is False


def test_responde_503_quando_banco_falha(client, monkeypatch, tesseract_com_portugues):
    class ConexaoIndisponivel:
        def cursor(self):
            raise OperationalError("banco indisponível")

    monkeypatch.setattr(views, "connection", ConexaoIndisponivel())

    resposta = client.get(reverse("healthz"))

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "falha", "verificacoes": {"banco": False, "tesseract_por": True}}


def test_rejeita_metodos_diferentes_de_get(client):
    resposta = client.post(reverse("healthz"))

    assert resposta.status_code == 405
