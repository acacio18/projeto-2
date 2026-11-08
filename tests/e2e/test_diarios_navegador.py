"""Telas da E2 no Chromium: confirmar notas, trocar a versão vigente e caber em qualquer largura."""

import copy
import json

import pytest
from playwright.sync_api import expect

from apps.academico.models import CoordenacaoCurso
from apps.importacao import servicos as versoes
from tests.apoio.boletins import carregar_gabarito
from tests.apoio.fabricas import (
    SENHA_PADRAO,
    AdminFactory,
    CoordenadorFactory,
    ProfessorFactory,
    TurmaFactory,
)

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def _entrar(page, base, email):
    page.goto(f"{base}/entrar/")
    page.get_by_label("E-mail institucional").fill(email)
    page.get_by_label("Senha", exact=True).fill(SENHA_PADRAO)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("heading", level=1)).to_contain_text("Olá")


def _sem_rolagem_horizontal(page) -> bool:
    return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_professor_confirma_as_notas_e_volta_para_a_versao_anterior(page, live_server):
    professor = ProfessorFactory(email="prof@ifpb.edu.br")
    dados = carregar_gabarito()
    v1 = versoes.registrar_versao(por=professor, dados=dados, bimestre_corte=4, sha256="a" * 64)
    _entrar(page, live_server.url, "prof@ifpb.edu.br")

    page.get_by_role("link", name="Diários", exact=True).click()
    expect(page.get_by_text("aguardando confirmação", exact=True)).to_be_visible()
    page.get_by_role("link", name="Análise e Projeto de Sistema").click()
    expect(page.get_by_text("Boletim aguardando confirmação")).to_be_visible()
    expect(page.get_by_role("rowheader", name="Aline Santana Ramos de Jesus 201927621032")).to_be_visible()
    page.get_by_role("button", name="Confirmar notas").click()
    expect(page.get_by_text("Notas confirmadas como versão 1, agora vigente.")).to_be_visible()

    corrigido = copy.deepcopy(dados)
    corrigido["alunos"][0]["etapas"][0]["nota"] = 60
    v2 = versoes.registrar_versao(por=professor, dados=corrigido, bimestre_corte=4, sha256="b" * 64)
    versoes.confirmar_versao(por=professor, importacao=v2)
    page.reload()
    expect(page.get_by_role("heading", name="Notas da versão 2")).to_be_visible()
    page.get_by_role("link", name="Versão 1", exact=True).click()
    expect(page.get_by_role("heading", name="Notas da versão 1")).to_be_visible()
    page.get_by_role("button", name="Tornar esta versão a vigente").click()
    expect(page.get_by_text("A versão 1 passou a ser a vigente.")).to_be_visible()
    v1.refresh_from_db()
    assert v1.vigente


@pytest.mark.parametrize("largura", [375, 768, 1024, 1440])
def test_telas_da_e2_sem_rolagem_horizontal(page, live_server, largura):
    admin = AdminFactory(email="admin@ifpb.edu.br")
    coordenador = CoordenadorFactory()
    importacao = versoes.registrar_versao(
        por=ProfessorFactory(), dados=carregar_gabarito(), bimestre_corte=4, sha256="a" * 64
    )
    diario = importacao.diario
    CoordenacaoCurso.objects.create(curso=diario.curso, usuario=coordenador)
    turma = TurmaFactory(curso=diario.curso, ano_letivo=diario.ano_letivo)
    page.set_viewport_size({"width": largura, "height": 800})
    _entrar(page, live_server.url, admin.email)
    caminhos = [
        "/painel/",
        "/diarios/",
        f"/diarios/{diario.pk}/",
        f"/diarios/{diario.pk}/editar/",
        "/cadastros/",
        "/cadastros/cursos/",
        f"/cadastros/cursos/{diario.curso_id}/",
        "/cadastros/turmas/",
        f"/cadastros/turmas/{turma.pk}/",
        "/cadastros/disciplinas/",
    ]
    for caminho in caminhos:
        page.goto(f"{live_server.url}{caminho}")
        assert _sem_rolagem_horizontal(page), f"{caminho} em {largura}px"


def test_tabela_de_notas_rola_dentro_do_quadro_no_celular(page, live_server):
    professor = ProfessorFactory(email="prof@ifpb.edu.br")
    importacao = versoes.registrar_versao(
        por=professor, dados=carregar_gabarito(), bimestre_corte=4, sha256="a" * 64
    )
    page.set_viewport_size({"width": 375, "height": 800})
    _entrar(page, live_server.url, "prof@ifpb.edu.br")
    page.goto(f"{live_server.url}/diarios/{importacao.diario_id}/")
    quadro = page.locator(".tabela-rolavel").last
    medidas = json.loads(quadro.evaluate("q => JSON.stringify([q.scrollWidth, q.clientWidth])"))
    assert medidas[0] > medidas[1]  # a tabela é mais larga que o quadro, que rola
    assert _sem_rolagem_horizontal(page)  # mas a página não
