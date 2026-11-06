"""Telas da E1 no Chromium: fluxo do convite, responsividade, menu, tema, senha e teclado."""

import re

import pytest
from playwright.sync_api import expect

from tests.apoio.fabricas import SENHA_PADRAO, AdminFactory, ProfessorFactory

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

LARGURAS = [375, 768, 1024, 1440]


def _entrar(page, base, email, senha=SENHA_PADRAO):
    page.goto(f"{base}/entrar/")
    page.get_by_label("E-mail institucional").fill(email)
    page.get_by_label("Senha", exact=True).fill(senha)
    page.get_by_role("button", name="Entrar").click()


def _sem_rolagem_horizontal(page) -> bool:
    return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_admin_convida_professor_que_cria_a_senha_e_entra(page, live_server, mailoutbox):
    AdminFactory(email="admin@ifpb.edu.br", nome="Ada Admin")
    _entrar(page, live_server.url, "admin@ifpb.edu.br")
    expect(page.get_by_role("heading", name="Olá, Ada")).to_be_visible()

    page.get_by_role("link", name="Novo usuário").first.click()
    page.get_by_label("Nome completo").fill("Paulo Professor")
    page.get_by_label("E-mail institucional").fill("paulo@ifpb.edu.br")
    page.get_by_label("Perfil").select_option("PROFESSOR")
    page.get_by_role("button", name="Cadastrar e enviar convite").click()
    expect(page.get_by_text("Convite enviado para paulo@ifpb.edu.br")).to_be_visible()
    expect(page.get_by_text("Convite pendente").first).to_be_visible()
    page.get_by_role("button", name="Sair").click()
    expect(page.get_by_text("Você saiu do SUAP V2.")).to_be_visible()

    link = re.search(r"https?://\S+", mailoutbox[0].body).group(0)
    page.goto(link)
    nova = "senha-do-paulo-2026"
    page.get_by_label("Nova senha", exact=True).fill(nova)
    page.get_by_label("Confirmação da nova senha").fill(nova)
    page.get_by_role("button", name="Salvar senha").click()
    expect(page.get_by_role("heading", name="Senha criada")).to_be_visible()

    _entrar(page, live_server.url, "paulo@ifpb.edu.br", nova)
    expect(page.get_by_text("Você entrou como Professor")).to_be_visible()
    expect(page.get_by_role("link", name="Usuários")).to_have_count(0)


@pytest.mark.parametrize("largura", LARGURAS)
def test_sem_rolagem_horizontal_em_nenhuma_largura(page, live_server, largura):
    AdminFactory(email="admin@ifpb.edu.br")
    alvo = ProfessorFactory(
        nome="Maria Aparecida dos Santos Albuquerque de Vasconcelos",
        email="maria.aparecida.vasconcelos@ifpb.edu.br",
    )
    page.set_viewport_size({"width": largura, "height": 800})
    page.goto(f"{live_server.url}/entrar/")
    assert _sem_rolagem_horizontal(page)
    _entrar(page, live_server.url, "admin@ifpb.edu.br")
    for caminho in ["/painel/", "/usuarios/", "/usuarios/novo/", f"/usuarios/{alvo.pk}/", "/senha/alterar/"]:
        page.goto(f"{live_server.url}{caminho}")
        assert _sem_rolagem_horizontal(page), f"{caminho} em {largura}px"


@pytest.mark.parametrize("largura", [375, 768])
def test_menu_no_celular_e_tablet(page, live_server, largura):
    AdminFactory(email="admin@ifpb.edu.br")
    page.set_viewport_size({"width": largura, "height": 800})
    _entrar(page, live_server.url, "admin@ifpb.edu.br")
    usuarios = page.get_by_role("link", name="Usuários", exact=True)
    expect(usuarios).to_be_hidden()
    botao = page.get_by_role("button", name="Abrir menu de navegação")
    botao.click()
    expect(botao).to_have_attribute("aria-expanded", "true")
    expect(usuarios).to_be_visible()


def test_tema_escuro_e_guardado(page, live_server):
    ProfessorFactory(email="prof@ifpb.edu.br")
    page.emulate_media(color_scheme="light")
    _entrar(page, live_server.url, "prof@ifpb.edu.br")
    botao = page.locator("[data-alternar-tema]")
    expect(botao).to_have_attribute("aria-pressed", "false")
    botao.click()
    expect(page.locator("html")).to_have_attribute("data-tema", "escuro")
    page.reload()
    expect(page.locator("html")).to_have_attribute("data-tema", "escuro")
    expect(botao).to_have_attribute("aria-pressed", "true")
    fundo = page.evaluate("getComputedStyle(document.body).backgroundColor")
    assert fundo == "rgb(11, 17, 32)"


def test_mostrar_senha(page, live_server):
    page.goto(f"{live_server.url}/entrar/")
    campo = page.get_by_label("Senha", exact=True)
    campo.fill("segredo")
    expect(campo).to_have_attribute("type", "password")
    page.get_by_role("button", name="Mostrar senha").click()
    expect(campo).to_have_attribute("type", "text")
    expect(page.get_by_role("button", name="Ocultar senha")).to_have_attribute("aria-pressed", "true")


def test_teclado_link_de_pular_e_foco_visivel(page, live_server):
    # O login põe o foco direto no e-mail (autofocus); o link de pular é o 1º Tab nas demais páginas.
    ProfessorFactory(email="prof@ifpb.edu.br")
    _entrar(page, live_server.url, "prof@ifpb.edu.br")
    page.goto(f"{live_server.url}/painel/")
    page.keyboard.press("Tab")
    pular = page.get_by_role("link", name="Pular para o conteúdo")
    expect(pular).to_be_focused()
    expect(pular).to_be_in_viewport()
    contorno = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
    assert contorno != "none"  # foco visível em link
    page.goto(f"{live_server.url}/senha/alterar/")
    page.keyboard.press("Tab")
    page.get_by_label("Senha atual").focus()
    sombra = page.evaluate("getComputedStyle(document.activeElement).boxShadow")
    assert sombra != "none"  # anel de foco visível no campo


def test_senha_errada_mostra_erro_e_botao_nao_trava(page, live_server):
    ProfessorFactory(email="prof@ifpb.edu.br")
    _entrar(page, live_server.url, "prof@ifpb.edu.br", "errada")
    expect(page.get_by_role("alert")).to_contain_text("E-mail ou senha incorretos")
    expect(page.get_by_role("button", name="Entrar")).not_to_have_attribute("aria-busy", "true")


def test_botao_de_menu_some_no_desktop(page, live_server):
    ProfessorFactory(email="prof@ifpb.edu.br")
    page.set_viewport_size({"width": 1440, "height": 800})
    _entrar(page, live_server.url, "prof@ifpb.edu.br")
    expect(page.get_by_role("button", name="Abrir menu de navegação")).to_be_hidden()
    expect(page.get_by_role("link", name="Alterar senha")).to_be_visible()
