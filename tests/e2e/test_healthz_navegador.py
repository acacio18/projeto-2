"""Teste de ponta a ponta: o /healthz responde a um navegador real."""

import subprocess

import pytest
from playwright.sync_api import Page, expect

from apps.ops import views

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def test_healthz_abre_no_navegador(page: Page, live_server, monkeypatch):
    def tesseract_com_portugues(*args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="eng\nosd\npor\n", stderr="")

    monkeypatch.setattr(views.subprocess, "run", tesseract_com_portugues)

    resposta = page.goto(f"{live_server.url}/healthz")

    assert resposta is not None
    assert resposta.status == 200
    expect(page.locator("body")).to_contain_text('"status": "ok"')
