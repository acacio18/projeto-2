"""Capturas das telas para a revisão visual (Pre-Delivery Checklist da skill UI/UX Pro Max).

Só roda com a variável SUAP_CAPTURAS apontando para a pasta de saída:
    $env:SUAP_CAPTURAS = "docs\\evidencias\\E1-telas"
    .venv\\Scripts\\python -m pytest tests/e2e/test_capturas_telas.py
"""

import os
from pathlib import Path

import pytest

from apps.contas.models import Perfil
from tests.apoio.fabricas import SENHA_PADRAO, AdminFactory, CoordenadorFactory, ProfessorFactory

PASTA = os.environ.get("SUAP_CAPTURAS")
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not PASTA, reason="defina SUAP_CAPTURAS para gerar as capturas"),
]


def _foto(page, nome, largura, tema="claro", altura=900):
    page.set_viewport_size({"width": largura, "height": altura})
    # Sem animação: senão a foto pega a transição de 200 ms entre os temas pela metade.
    page.emulate_media(color_scheme="dark" if tema == "escuro" else "light", reduced_motion="reduce")
    page.evaluate("document.documentElement.removeAttribute('data-tema')")
    page.wait_for_timeout(50)
    page.screenshot(path=str(Path(PASTA) / f"{nome}-{largura}-{tema}.png"), full_page=True)


def test_capturas(page, live_server):
    base = live_server.url
    AdminFactory(email="ada.admin@ifpb.edu.br", nome="Ada Lovelace")
    CoordenadorFactory(nome="Carlos Drummond de Andrade", email="carlos.drummond@ifpb.edu.br")
    for numero, nome in enumerate(
        ["Cecília Meireles", "Graciliano Ramos", "Rachel de Queiroz", "José Lins do Rego"]
    ):
        ProfessorFactory(nome=nome, email=f"professor{numero}@ifpb.edu.br")
    convidado = ProfessorFactory(nome="Ariano Suassuna", email="ariano.suassuna@ifpb.edu.br")
    convidado.set_unusable_password()
    convidado.save()
    ProfessorFactory(nome="Augusto dos Anjos", email="augusto.anjos@ifpb.edu.br", is_active=False)

    page.goto(f"{base}/entrar/")
    for largura, tema in [(375, "claro"), (1440, "claro"), (1440, "escuro")]:
        _foto(page, "01-entrar", largura, tema)
    page.get_by_label("E-mail institucional").fill("ada.admin@ifpb.edu.br")
    page.get_by_label("Senha", exact=True).fill("senha-errada")
    page.get_by_role("button", name="Entrar").click()
    _foto(page, "02-entrar-erro", 768)

    page.get_by_label("E-mail institucional").fill("ada.admin@ifpb.edu.br")
    page.get_by_label("Senha", exact=True).fill(SENHA_PADRAO)
    page.get_by_role("button", name="Entrar").click()
    for largura, tema in [(1440, "claro"), (1440, "escuro"), (375, "claro")]:
        _foto(page, "03-painel-admin", largura, tema)
    page.set_viewport_size({"width": 375, "height": 900})
    page.get_by_role("button", name="Abrir menu de navegação").click()
    _foto(page, "04-menu-aberto", 375)

    page.goto(f"{base}/usuarios/")
    for largura, tema in [(1440, "claro"), (1440, "escuro"), (1024, "claro"), (375, "claro")]:
        _foto(page, "05-usuarios", largura, tema)

    page.goto(f"{base}/usuarios/novo/")
    page.get_by_label("E-mail institucional").fill("alguem@gmail.com")
    page.get_by_label("Perfil").select_option(Perfil.PROFESSOR)
    page.get_by_role("button", name="Cadastrar e enviar convite").click()
    for largura, tema in [(768, "claro"), (768, "escuro")]:
        _foto(page, "06-novo-usuario-erros", largura, tema)

    page.goto(f"{base}/usuarios/{convidado.pk}/")
    for largura, tema in [(1440, "claro"), (375, "escuro")]:
        _foto(page, "07-editar-usuario", largura, tema)
    page.goto(f"{base}/usuarios/{convidado.pk}/desativar/")
    _foto(page, "08-confirmar-desativacao", 1024)

    page.goto(f"{base}/senha/alterar/")
    _foto(page, "09-alterar-senha", 1024, "escuro")
    page.goto(f"{base}/usuarios/999999/")
    _foto(page, "10-nao-encontrado", 768)
