"""Telas de acesso: entrar, sair, CSRF, sessão expirada, bloqueio e senhas (IDs 1 e 13)."""

import re
from datetime import timedelta

import pytest
from axes.models import AccessAttempt
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.auditoria.models import EventoAuditoria, TipoEvento
from tests.apoio.fabricas import SENHA_PADRAO, AdminFactory, CoordenadorFactory, ProfessorFactory

pytestmark = pytest.mark.django_db

URL_ENTRAR = reverse("contas:entrar")
URL_PAINEL = reverse("painel")


def _entrar(client, email, senha=SENHA_PADRAO, **extra):
    return client.post(URL_ENTRAR, {"username": email, "password": senha, **extra})


def _link_do_email(mensagem) -> str:
    return re.search(r"https?://\S+", mensagem.body).group(0)


def test_pagina_de_login_e_acessivel(client):
    html = client.get(URL_ENTRAR).content.decode()
    assert '<label class="campo__rotulo" for="id_username">E-mail institucional</label>' in html
    assert 'type="email"' in html
    assert 'autocomplete="username"' in html
    assert 'autocomplete="current-password"' in html
    assert 'href="#conteudo"' in html  # link "pular para o conteúdo"
    assert "csrfmiddlewaretoken" in html


def test_anonimo_e_levado_ao_login(client):
    assert client.get("/").url == URL_PAINEL
    resposta = client.get(URL_PAINEL)
    assert resposta.status_code == 302
    assert resposta.url == f"{URL_ENTRAR}?next={URL_PAINEL}"


@pytest.mark.parametrize(
    ("fabrica", "perfil", "ve_usuarios"),
    [
        (AdminFactory, "Administrador", True),
        (CoordenadorFactory, "Coordenador", False),
        (ProfessorFactory, "Professor", False),
    ],
)
def test_cada_perfil_entra_e_cai_no_seu_painel(client, fabrica, perfil, ve_usuarios):
    usuario = fabrica(nome="Fulana de Tal")
    resposta = _entrar(client, usuario.email.upper())
    assert resposta.status_code == 302
    assert resposta.url == URL_PAINEL
    html = client.get(URL_PAINEL).content.decode()
    assert "Olá, Fulana" in html
    assert f"<strong>{perfil}</strong>" in html
    assert (reverse("usuarios:lista") in html) is ve_usuarios
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.LOGIN_SUCESSO, usuario=usuario).exists()


def test_next_seguro_e_respeitado_e_externo_e_ignorado(client):
    admin = AdminFactory()
    assert _entrar(client, admin.email, next="/usuarios/").url == "/usuarios/"
    client.post(reverse("contas:sair"))
    assert _entrar(client, admin.email, next="https://exemplo.com/").url == URL_PAINEL


def test_senha_errada_mostra_mensagem_generica(client):
    ProfessorFactory(email="ana@ifpb.edu.br")
    html = _entrar(client, "ana@ifpb.edu.br", "errada").content.decode()
    assert "E-mail ou senha incorretos" in html
    assert 'role="alert"' in html


def test_usuario_desativado_recebe_a_mesma_mensagem(client):
    ProfessorFactory(email="saiu@ifpb.edu.br", is_active=False)
    assert "E-mail ou senha incorretos" in _entrar(client, "saiu@ifpb.edu.br").content.decode()


def test_quem_ja_entrou_nao_ve_o_login_de_novo(client):
    client.force_login(ProfessorFactory())
    assert client.get(URL_ENTRAR).url == URL_PAINEL


def test_cinco_erros_bloqueiam_e_a_tela_explica(client):
    ProfessorFactory(email="bia@ifpb.edu.br")
    for _ in range(5):
        _entrar(client, "bia@ifpb.edu.br", "errada")
    resposta = _entrar(client, "bia@ifpb.edu.br")  # senha certa, mas bloqueada
    assert resposta.status_code == 429
    assert "Acesso bloqueado temporariamente" in resposta.content.decode()


def test_sair_exige_post_e_registra(client):
    professor = ProfessorFactory()
    client.force_login(professor)
    assert client.get(reverse("contas:sair")).status_code == 405
    resposta = client.post(reverse("contas:sair"), follow=True)
    assert resposta.redirect_chain[-1][0] == URL_ENTRAR
    assert "Você saiu do SUAP V2." in resposta.content.decode()
    assert client.get(URL_PAINEL).status_code == 302
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.LOGOUT, usuario=professor).exists()


def test_post_sem_token_csrf_e_recusado():
    cliente = Client(enforce_csrf_checks=True)
    resposta = cliente.post(URL_ENTRAR, {"username": "x@ifpb.edu.br", "password": "x"})
    assert resposta.status_code == 403
    assert "Formulário expirado" in resposta.content.decode()


def test_sessao_expira_por_inatividade(client, settings):
    assert settings.SESSION_COOKIE_AGE == 30 * 60
    assert settings.SESSION_SAVE_EVERY_REQUEST  # cada acesso renova o prazo
    client.force_login(ProfessorFactory())
    assert client.get(URL_PAINEL).status_code == 200
    sessao = client.session
    sessao.set_expiry(timezone.now() - timedelta(seconds=1))
    sessao.save()
    assert client.get(URL_PAINEL).status_code == 302


def test_alterar_senha(client):
    professor = ProfessorFactory()
    client.force_login(professor)
    url = reverse("contas:alterar_senha")
    errada = client.post(url, {"old_password": "nao", "new_password1": "x", "new_password2": "x"})
    assert 'aria-invalid="true"' in errada.content.decode()
    nova = "uma-senha-bem-nova-2026"
    resposta = client.post(url, {"old_password": SENHA_PADRAO, "new_password1": nova, "new_password2": nova})
    assert resposta.url == URL_PAINEL
    professor.refresh_from_db()
    assert professor.check_password(nova)
    assert client.get(URL_PAINEL).status_code == 200  # continua conectado
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.SENHA_ALTERADA, usuario=professor).exists()


def test_alterar_senha_exige_login(client):
    assert client.get(reverse("contas:alterar_senha")).status_code == 302


def test_esqueci_senha_responde_igual_para_quem_existe_ou_nao(client):
    ProfessorFactory(email="existe@ifpb.edu.br")
    url = reverse("contas:esqueci_senha")
    r1 = client.post(url, {"email": "existe@ifpb.edu.br"})
    r2 = client.post(url, {"email": "naoexiste@ifpb.edu.br"})
    assert r1.url == r2.url == reverse("contas:esqueci_senha_enviado")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["existe@ifpb.edu.br"]
    assert mail.outbox[0].subject == "Criar nova senha no SUAP V2"
    pedidos = EventoAuditoria.objects.filter(tipo=TipoEvento.SENHA_REDEFINICAO_PEDIDA)
    assert sorted(pedidos.values_list("email_informado", flat=True)) == [
        "existe@ifpb.edu.br",
        "naoexiste@ifpb.edu.br",
    ]
    assert "72 horas" in client.get(r1.url).content.decode()


def test_link_de_redefinicao_cria_senha_desbloqueia_e_vale_uma_vez(client):
    professor = ProfessorFactory(email="esqueceu@ifpb.edu.br")
    for _ in range(5):
        _entrar(client, professor.email, "errada")
    client.post(reverse("contas:esqueci_senha"), {"email": professor.email})
    link = _link_do_email(mail.outbox[0])
    formulario = client.get(link, follow=True)
    assert "Criar senha" in formulario.content.decode()
    url_formulario = formulario.redirect_chain[-1][0]
    nova = "senha-nova-depois-de-esquecer"
    diferente = client.post(url_formulario, {"new_password1": nova, "new_password2": nova + "x"})
    assert 'aria-invalid="true"' in diferente.content.decode()
    resposta = client.post(url_formulario, {"new_password1": nova, "new_password2": nova})
    assert resposta.url == reverse("contas:senha_definida")
    assert not AccessAttempt.objects.filter(username=professor.email).exists()
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.SENHA_DEFINIDA, usuario=professor).exists()
    assert _entrar(client, professor.email, nova).url == URL_PAINEL
    client.post(reverse("contas:sair"))
    assert "Link inválido ou vencido" in client.get(link, follow=True).content.decode()


def test_link_invalido(client):
    url = reverse("contas:definir_senha", kwargs={"uidb64": "MQ", "token": "token-falso"})
    assert "Link inválido ou vencido" in client.get(url).content.decode()


def test_quem_ainda_nao_aceitou_o_convite_nao_recebe_redefinicao(client):
    convidado = ProfessorFactory(email="convidado@ifpb.edu.br")
    convidado.set_unusable_password()
    convidado.save()
    client.post(reverse("contas:esqueci_senha"), {"email": "convidado@ifpb.edu.br"})
    assert mail.outbox == []  # usa o convite (reenviado pelo administrador)
