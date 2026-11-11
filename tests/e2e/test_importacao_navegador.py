"""Importação no Chromium: o professor envia o PDF, acompanha a leitura e confirma as notas."""

import pytest
from playwright.sync_api import expect

from apps.importacao.models import Importacao
from tests.apoio.boletins import BOLETIM_EXEMPLO
from tests.apoio.fabricas import SENHA_PADRAO, ProfessorFactory

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.fixture(autouse=True)
def midia(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path / "midia")


def test_professor_envia_o_boletim_e_confirma_as_notas(page, live_server):
    ProfessorFactory(email="prof@ifpb.edu.br")
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("E-mail institucional").fill("prof@ifpb.edu.br")
    page.get_by_label("Senha", exact=True).fill(SENHA_PADRAO)
    page.get_by_role("button", name="Entrar").click()

    page.get_by_role("link", name="Enviar boletins").first.click()
    page.get_by_label("Boletins do SUAP (PDF)").set_input_files(str(BOLETIM_EXEMPLO))
    page.get_by_label("Até qual bimestre as notas estão fechadas?").select_option("2")
    page.get_by_role("button", name="Enviar e ler").click()

    # A fila roda na hora nos testes; a página de acompanhamento leva direto à conferência.
    expect(page.get_by_text("Boletim aguardando confirmação")).to_be_visible(timeout=15000)
    expect(page.get_by_text("Lido pelo texto do PDF.")).to_be_visible()
    expect(page.get_by_text("depois do bimestre informado (2º)")).to_be_visible()
    page.get_by_role("button", name="Confirmar notas").click()
    expect(page.get_by_text("Notas confirmadas como versão 1, agora vigente.")).to_be_visible()
    importacao = Importacao.objects.get()
    assert (importacao.numero_versao, importacao.vigente, importacao.bimestre_corte) == (1, True, 2)


@pytest.mark.parametrize("largura", [375, 768, 1024, 1440])
def test_telas_da_e3_sem_rolagem_horizontal(page, live_server, largura):
    ProfessorFactory(email="prof@ifpb.edu.br")
    page.set_viewport_size({"width": largura, "height": 800})
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("E-mail institucional").fill("prof@ifpb.edu.br")
    page.get_by_label("Senha", exact=True).fill(SENHA_PADRAO)
    page.get_by_role("button", name="Entrar").click()
    for caminho in ["/importacoes/enviar/", "/importacoes/"]:
        page.goto(f"{live_server.url}{caminho}")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), caminho
