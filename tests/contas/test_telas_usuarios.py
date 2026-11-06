"""Telas do cadastro de usuários (ID 15) e matriz de permissões (ID 2)."""

import re
from smtplib import SMTPException

import pytest
from axes.models import AccessAttempt
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from apps.auditoria.models import EventoAuditoria, TipoEvento
from apps.contas import servicos
from apps.contas.models import Perfil, Usuario
from tests.apoio.fabricas import SENHA_PADRAO, AdminFactory, CoordenadorFactory, ProfessorFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin():
    return AdminFactory(nome="Admin Principal")


@pytest.fixture
def cliente_admin(client, admin):
    client.force_login(admin)
    return client


def _rotas(pk):
    """(método, url) de todas as rotas do cadastro."""
    return [
        ("get", reverse("usuarios:lista")),
        ("get", reverse("usuarios:novo")),
        ("post", reverse("usuarios:novo")),
        ("get", reverse("usuarios:editar", args=[pk])),
        ("get", reverse("usuarios:desativar", args=[pk])),
        ("post", reverse("usuarios:reativar", args=[pk])),
        ("post", reverse("usuarios:reenviar_convite", args=[pk])),
        ("post", reverse("usuarios:desbloquear", args=[pk])),
    ]


@pytest.mark.parametrize("quem", ["anonimo", "professor", "coordenador", "admin"])
def test_matriz_de_permissoes(client, quem):
    alvo = ProfessorFactory()
    esperado = {"anonimo": 302, "professor": 403, "coordenador": 403}
    if quem != "anonimo":
        fabrica = {"professor": ProfessorFactory, "coordenador": CoordenadorFactory, "admin": AdminFactory}[
            quem
        ]
        client.force_login(fabrica())
    for metodo, url in _rotas(alvo.pk):
        resposta = getattr(client, metodo)(url)
        if quem == "anonimo":
            assert resposta.status_code == 302, url
            assert resposta.url.startswith(reverse("contas:entrar")), url
        elif quem == "admin":
            assert resposta.status_code in (200, 302), url
        else:
            assert resposta.status_code == esperado[quem], url


def test_registro_inexistente_responde_404(cliente_admin):
    for metodo, url in _rotas(999_999)[3:]:
        assert getattr(cliente_admin, metodo)(url).status_code == 404, url


def test_metodo_errado_responde_405(cliente_admin, admin):
    assert cliente_admin.get(reverse("usuarios:reativar", args=[admin.pk])).status_code == 405


def test_lista_com_busca_e_filtros(cliente_admin):
    ProfessorFactory(nome="Maria Dantas", email="maria@ifpb.edu.br")
    CoordenadorFactory(nome="Carlos Lima")
    ProfessorFactory(nome="Inativa Souza", is_active=False)
    convidado = ProfessorFactory(nome="Convidado Novo")
    convidado.set_unusable_password()
    convidado.save()
    url = reverse("usuarios:lista")

    def nomes(**filtros):
        pagina = cliente_admin.get(url, filtros).context["pagina"]
        return [u.nome for u in pagina]

    assert nomes(q="dantas") == ["Maria Dantas"]
    assert nomes(q="MARIA@") == ["Maria Dantas"]
    assert nomes(perfil=Perfil.COORDENADOR) == ["Carlos Lima"]
    assert nomes(situacao="desativados") == ["Inativa Souza"]
    assert nomes(situacao="convite") == ["Convidado Novo"]
    assert "Inativa Souza" not in nomes(situacao="ativos")
    html = cliente_admin.get(url).content.decode()
    for texto in ("Convite pendente", "Desativado", "você"):
        assert texto in html


def test_lista_pagina_de_25_em_25_mantendo_filtros(cliente_admin):
    for numero in range(30):
        ProfessorFactory(nome=f"Professor {numero:02d}")
    resposta = cliente_admin.get(reverse("usuarios:lista"), {"perfil": Perfil.PROFESSOR})
    assert len(resposta.context["pagina"]) == 25
    assert "perfil=PROFESSOR&amp;pagina=2" in resposta.content.decode()
    segunda = cliente_admin.get(reverse("usuarios:lista"), {"perfil": Perfil.PROFESSOR, "pagina": 2})
    assert len(segunda.context["pagina"]) == 5


def test_cadastro_envia_convite_e_o_convidado_cria_a_senha(cliente_admin, admin):
    client = Client()  # navegador do convidado
    resposta = cliente_admin.post(
        reverse("usuarios:novo"),
        {"nome": "Rita Alves", "email": "Rita.Alves@ifpb.edu.br", "perfil": Perfil.PROFESSOR},
    )
    rita = Usuario.objects.get(email="rita.alves@ifpb.edu.br")
    assert resposta.url == reverse("usuarios:editar", args=[rita.pk])
    assert rita.convite_pendente
    assert len(mail.outbox) == 1
    mensagem = mail.outbox[0]
    assert (mensagem.to, mensagem.subject) == (["rita.alves@ifpb.edu.br"], "Convite para acessar o SUAP V2")
    for trecho in ("Olá, Rita.", "perfil Professor", "72 horas"):
        assert trecho in mensagem.body
    tipos = list(EventoAuditoria.objects.filter(usuario=admin).values_list("tipo", flat=True))
    assert TipoEvento.USUARIO_CRIADO in tipos
    assert TipoEvento.CONVITE_ENVIADO in tipos

    link = re.search(r"https?://\S+", mensagem.body).group(0)
    formulario = client.get(link, follow=True)
    senha = "senha-da-rita-2026"
    client.post(formulario.redirect_chain[-1][0], {"new_password1": senha, "new_password2": senha})
    entrada = client.post(reverse("contas:entrar"), {"username": "rita.alves@ifpb.edu.br", "password": senha})
    assert entrada.url == reverse("painel")


def test_cadastro_com_erro_de_validacao(cliente_admin):
    ProfessorFactory(email="ja@ifpb.edu.br")
    html = cliente_admin.post(
        reverse("usuarios:novo"), {"nome": "", "email": "x@gmail.com", "perfil": "INVALIDO"}
    ).content.decode()
    assert "Corrija 3 campos destacados abaixo." in html
    assert html.count('aria-invalid="true"') == 3
    assert 'aria-describedby="id_email_ajuda id_email_erro"' in html
    duplicado = cliente_admin.post(
        reverse("usuarios:novo"), {"nome": "Outro", "email": "JA@ifpb.edu.br", "perfil": Perfil.PROFESSOR}
    ).content.decode()
    assert "Já existe um usuário com este e-mail." in duplicado
    assert mail.outbox == []


def test_falha_no_envio_do_convite_avisa_e_mantem_o_cadastro(cliente_admin, monkeypatch):
    def falhar(*args, **kwargs):
        raise SMTPException("servidor fora do ar")

    monkeypatch.setattr(servicos, "send_mail", falhar)
    resposta = cliente_admin.post(
        reverse("usuarios:novo"),
        {"nome": "Sem Email", "email": "sem@ifpb.edu.br", "perfil": Perfil.PROFESSOR},
        follow=True,
    )
    html = resposta.content.decode()
    assert Usuario.objects.filter(email="sem@ifpb.edu.br").exists()
    assert "Não foi possível enviar o e-mail de convite" in html
    assert not EventoAuditoria.objects.filter(tipo=TipoEvento.CONVITE_ENVIADO).exists()


def test_edicao(cliente_admin):
    alvo = ProfessorFactory(nome="Nome Velho")
    url = reverse("usuarios:editar", args=[alvo.pk])
    assert "Nome Velho" in cliente_admin.get(url).content.decode()
    resposta = cliente_admin.post(
        url, {"nome": "Nome Novo", "email": alvo.email, "perfil": Perfil.COORDENADOR}, follow=True
    )
    assert "Alterações salvas." in resposta.content.decode()
    alvo.refresh_from_db()
    assert (alvo.nome, alvo.perfil) == ("Nome Novo", Perfil.COORDENADOR)
    invalido = cliente_admin.post(
        url, {"nome": "Outro Nome", "email": "x@gmail.com", "perfil": Perfil.PROFESSOR}
    )
    assert "<h1>Nome Novo</h1>" in invalido.content.decode()  # cabeçalho mostra o que está salvo


def test_admin_nao_se_rebaixa_sendo_o_unico(cliente_admin, admin):
    url = reverse("usuarios:editar", args=[admin.pk])
    html = cliente_admin.post(
        url, {"nome": admin.nome, "email": admin.email, "perfil": Perfil.PROFESSOR}
    ).content.decode()
    assert "O sistema precisa de pelo menos um administrador ativo." in html
    admin.refresh_from_db()
    assert admin.perfil == Perfil.ADMIN


def test_desativar_com_confirmacao_e_reativar(cliente_admin):
    alvo = ProfessorFactory(nome="Paula Reis")
    confirmar = cliente_admin.get(reverse("usuarios:desativar", args=[alvo.pk])).content.decode()
    assert "Desativar Paula Reis?" in confirmar
    resposta = cliente_admin.post(reverse("usuarios:desativar", args=[alvo.pk]), follow=True)
    assert "foi desativado" in resposta.content.decode()
    alvo.refresh_from_db()
    assert not alvo.is_active
    resposta = cliente_admin.post(reverse("usuarios:reativar", args=[alvo.pk]), follow=True)
    assert "foi reativado" in resposta.content.decode()
    alvo.refresh_from_db()
    assert alvo.is_active


def test_admin_nao_ve_botao_de_se_desativar_e_o_servidor_tambem_barra(cliente_admin, admin):
    url = reverse("usuarios:editar", args=[admin.pk])
    assert reverse("usuarios:desativar", args=[admin.pk]) not in cliente_admin.get(url).content.decode()
    resposta = cliente_admin.post(reverse("usuarios:desativar", args=[admin.pk]), follow=True)
    assert "Você não pode desativar a sua própria conta." in resposta.content.decode()


def test_reenviar_convite(cliente_admin):
    convidado = ProfessorFactory()
    convidado.set_unusable_password()
    convidado.save()
    url_editar = reverse("usuarios:editar", args=[convidado.pk])
    assert "Reenviar convite" in cliente_admin.get(url_editar).content.decode()
    resposta = cliente_admin.post(reverse("usuarios:reenviar_convite", args=[convidado.pk]), follow=True)
    assert "Convite enviado" in resposta.content.decode()
    assert len(mail.outbox) == 1


def test_nao_reenvia_convite_para_quem_ja_tem_senha_nem_para_desativado(cliente_admin):
    com_senha = ProfessorFactory()
    resposta = cliente_admin.post(reverse("usuarios:reenviar_convite", args=[com_senha.pk]), follow=True)
    assert "já definiu a senha" in resposta.content.decode()
    desativado = ProfessorFactory(is_active=False)
    desativado.set_unusable_password()
    desativado.save()
    resposta = cliente_admin.post(reverse("usuarios:reenviar_convite", args=[desativado.pk]), follow=True)
    assert "Reative o usuário antes" in resposta.content.decode()
    assert mail.outbox == []


def test_desbloquear_login(cliente_admin):
    client = Client()  # outro navegador: o do admin já está logado e seria redirecionado
    alvo = ProfessorFactory(email="trancado@ifpb.edu.br")
    for _ in range(5):
        client.post(reverse("contas:entrar"), {"username": alvo.email, "password": "errada"})
    url_editar = reverse("usuarios:editar", args=[alvo.pk])
    assert "Bloqueado por tentativas" in cliente_admin.get(url_editar).content.decode()
    resposta = cliente_admin.post(reverse("usuarios:desbloquear", args=[alvo.pk]), follow=True)
    assert "desbloqueado" in resposta.content.decode()
    assert not AccessAttempt.objects.filter(username=alvo.email).exists()
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.LOGIN_DESBLOQUEADO, objeto_id=str(alvo.pk)).exists()
    entrada = client.post(reverse("contas:entrar"), {"username": alvo.email, "password": SENHA_PADRAO})
    assert entrada.url == reverse("painel")


def test_painel_do_admin_resume_os_usuarios(cliente_admin):
    ProfessorFactory.create_batch(2)
    CoordenadorFactory()
    convidado = ProfessorFactory()
    convidado.set_unusable_password()
    convidado.save()
    ProfessorFactory(is_active=False)
    resumo = cliente_admin.get(reverse("painel")).context["resumo_usuarios"]
    assert resumo == {"ativos": 5, "professores": 3, "coordenadores": 1, "convites": 1}


def test_recusa_do_servico_aparece_no_formulario(cliente_admin, monkeypatch):
    """Ex.: outro administrador cadastrou o mesmo e-mail entre a validação e a gravação."""

    def recusar(**kwargs):
        raise ValidationError("Já existe um usuário com este e-mail.")

    monkeypatch.setattr(servicos, "criar_usuario", recusar)
    html = cliente_admin.post(
        reverse("usuarios:novo"),
        {"nome": "Corrida", "email": "corrida@ifpb.edu.br", "perfil": Perfil.PROFESSOR},
    ).content.decode()
    assert "Já existe um usuário com este e-mail." in html
    assert mail.outbox == []
