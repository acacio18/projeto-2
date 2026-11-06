"""Bloqueio por tentativas (django-axes): 5 falhas seguidas bloqueiam a conta."""

import pytest
from axes.models import AccessAttempt
from django.contrib.auth import authenticate, login
from django.contrib.sessions.middleware import SessionMiddleware

from apps.auditoria.models import EventoAuditoria, TipoEvento
from apps.contas.autenticacao import email_da_tentativa
from tests.apoio.fabricas import SENHA_PADRAO, ProfessorFactory

pytestmark = pytest.mark.django_db


def _tentar(rf, email, senha, ip="10.0.0.1"):
    return authenticate(rf.post("/entrar/", REMOTE_ADDR=ip), username=email, password=senha)


def test_cinco_falhas_bloqueiam_a_conta_mesmo_com_a_senha_certa(rf):
    professor = ProfessorFactory(email="bloqueio@ifpb.edu.br")
    for _ in range(5):
        assert _tentar(rf, "bloqueio@ifpb.edu.br", "errada") is None
    assert _tentar(rf, "bloqueio@ifpb.edu.br", SENHA_PADRAO) is None
    assert EventoAuditoria.objects.filter(
        tipo=TipoEvento.CONTA_BLOQUEADA, email_informado=professor.email
    ).exists()
    ultima = EventoAuditoria.objects.filter(tipo=TipoEvento.LOGIN_FALHA).order_by("-id").first()
    assert ultima.detalhes == {"conta_bloqueada": True}


def test_quatro_falhas_ainda_deixam_entrar_e_o_login_zera_a_contagem(rf):
    professor = ProfessorFactory(email="quase@ifpb.edu.br")
    for _ in range(4):
        _tentar(rf, "quase@ifpb.edu.br", "errada")
    requisicao = rf.post("/entrar/", REMOTE_ADDR="10.0.0.1")
    SessionMiddleware(lambda r: None).process_request(requisicao)
    usuario = authenticate(requisicao, username="quase@ifpb.edu.br", password=SENHA_PADRAO)
    assert usuario == professor
    assert AccessAttempt.objects.filter(username="quase@ifpb.edu.br").exists()
    login(requisicao, usuario)  # o django-axes zera a contagem no login efetivo
    assert not AccessAttempt.objects.filter(username="quase@ifpb.edu.br").exists()


def test_bloqueio_vale_quando_as_credenciais_chegam_pela_chave_email(rf):
    """Regressão: o axes monta as credenciais com o USERNAME_FIELD ("email") ao verificar o bloqueio."""
    ProfessorFactory(email="api@ifpb.edu.br")
    for _ in range(5):
        _tentar(rf, "api@ifpb.edu.br", "errada")
    requisicao = rf.post("/entrar/", REMOTE_ADDR="10.0.0.1")
    assert authenticate(requisicao, email="api@ifpb.edu.br", password=SENHA_PADRAO) is None


def test_bloqueio_vale_para_a_conta_em_qualquer_ip_e_grafia(rf):
    ProfessorFactory(email="conta@ifpb.edu.br")
    grafias = [
        "conta@ifpb.edu.br",
        "CONTA@ifpb.edu.br",
        " Conta@IFPB.edu.br",
        "conta@ifpb.edu.br",
        "conta@IFPB.EDU.BR",
    ]
    for numero, email in enumerate(grafias):
        _tentar(rf, email, "errada", ip=f"10.0.0.{numero + 1}")
    assert _tentar(rf, "conta@ifpb.edu.br", SENHA_PADRAO, ip="10.9.9.9") is None


def test_bloqueio_de_uma_conta_nao_afeta_outra_no_mesmo_ip(rf):
    ProfessorFactory(email="vitima@ifpb.edu.br")
    colega = ProfessorFactory(email="colega@ifpb.edu.br")
    for _ in range(5):
        _tentar(rf, "vitima@ifpb.edu.br", "errada", ip="200.1.1.1")
    assert _tentar(rf, "colega@ifpb.edu.br", SENHA_PADRAO, ip="200.1.1.1") == colega


@pytest.mark.parametrize(
    ("credenciais", "post", "esperado"),
    [
        ({"username": " Nome@IFPB.edu.br "}, {}, "nome@ifpb.edu.br"),
        ({"email": "Chave.Email@ifpb.edu.br"}, {}, "chave.email@ifpb.edu.br"),
        (None, {"username": "Form@IFPB.edu.br"}, "form@ifpb.edu.br"),
        ({}, {}, None),
    ],
)
def test_email_da_tentativa_normaliza(rf, credenciais, post, esperado):
    assert email_da_tentativa(rf.post("/", post), credenciais) == esperado


def test_email_da_tentativa_sem_requisicao():
    assert email_da_tentativa(None, None) is None
