"""A fila de verdade: um ``qcluster`` em outro processo lê o boletim enviado (Django-Q2 com broker ORM).

Os outros testes rodam a fila na hora, no mesmo processo (``sync``). Este confere a montagem de
produção e de desenvolvimento: a tarefa vai para a tabela da fila no PostgreSQL, o processo do
``qcluster`` (iniciado como no ``scripts/dev.ps1``) a executa e o gancho final roda.
"""

import os
import subprocess  # nosec B404 - inicia o próprio manage.py do projeto, sem entrada externa
import sys
import time
from pathlib import Path
from urllib.parse import quote

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django_q.conf import Conf

from apps.importacao import envio
from apps.importacao.models import Importacao, StatusImportacao
from tests.apoio.fabricas import ProfessorFactory

pytestmark = [pytest.mark.fila, pytest.mark.django_db(transaction=True)]

RAIZ = Path(__file__).resolve().parents[2]


def _url_do_banco_de_teste() -> str:
    d = connection.settings_dict
    usuario, senha = quote(d["USER"], safe=""), quote(d["PASSWORD"], safe="")
    return f"postgres://{usuario}:{senha}@{d['HOST'] or 'localhost'}:{d['PORT'] or 5432}/{d['NAME']}"


def _encerrar(processo: subprocess.Popen) -> None:
    if sys.platform == "win32":
        # o qcluster cria processos filhos: encerra a árvore inteira, como o dev.ps1
        subprocess.run(  # nosec B603 B607 - comando fixo do Windows, sem entrada externa
            ["taskkill", "/PID", str(processo.pid), "/T", "/F"], capture_output=True, check=False
        )
    else:
        processo.kill()
    processo.wait(timeout=30)


def test_qcluster_le_o_boletim_enviado(settings, tmp_path, monkeypatch, boletim_exemplo):
    settings.MEDIA_ROOT = str(tmp_path)
    monkeypatch.setattr(Conf, "SYNC", False)  # a tarefa vai para a fila no banco, não roda aqui
    lote = envio.receber_envio(
        por=ProfessorFactory(),
        arquivos_enviados=[SimpleUploadedFile("boletim.pdf", boletim_exemplo.read_bytes())],
        bimestre_corte=4,
    )
    importacao = lote.importacoes.get()
    assert importacao.status == StatusImportacao.RECEBIDA

    ambiente = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.dev",
        "DATABASE_URL": _url_do_banco_de_teste(),
        "DJANGO_MEDIA_ROOT": str(tmp_path),
        "FILA_PROCESSOS": "1",
    }
    processo = subprocess.Popen(  # nosec B603 - o próprio Python do .venv com o manage.py do projeto
        [sys.executable, str(RAIZ / "manage.py"), "qcluster"],
        cwd=RAIZ,
        env=ambiente,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        limite = time.monotonic() + 90
        while time.monotonic() < limite:
            importacao.refresh_from_db()
            if importacao.status not in (StatusImportacao.RECEBIDA, StatusImportacao.PROCESSANDO):
                break
            time.sleep(0.5)
    finally:
        _encerrar(processo)

    assert importacao.status == StatusImportacao.AGUARDANDO_CONFIRMACAO
    assert importacao.diario.codigo == "70764"
    assert importacao.relatorio_validacao["metodo"] == "TEXTO"
    assert Importacao.objects.count() == 1
