"""Eventos de auditoria: gravação, imutabilidade (Python e PostgreSQL) e eventos de login/logout."""

import pytest
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.db import DatabaseError, connection, transaction

from apps.auditoria.models import EventoAuditoria, EventoImutavelError, TipoEvento
from apps.auditoria.registro import registrar
from tests.apoio.fabricas import SENHA_PADRAO, ProfessorFactory

pytestmark = pytest.mark.django_db


def _requisicao(rf, ip="10.0.0.7", agente="Navegador de Teste/1.0"):
    return rf.post("/entrar/", REMOTE_ADDR=ip, HTTP_USER_AGENT=agente)


def test_registrar_grava_quem_quando_onde_e_o_objeto(rf):
    admin, alvo = ProfessorFactory(), ProfessorFactory()
    evento = registrar(
        TipoEvento.USUARIO_CRIADO, request=_requisicao(rf), usuario=admin, objeto=alvo, perfil="X"
    )
    evento.refresh_from_db()
    assert evento.usuario == admin
    assert (evento.objeto_tipo, evento.objeto_id) == ("contas.Usuario", str(alvo.pk))
    assert evento.ip == "10.0.0.7"
    assert evento.agente == "Navegador de Teste/1.0"
    assert evento.detalhes == {"perfil": "X"}
    assert evento.momento is not None
    assert "Usuário criado" in str(evento)


def test_registrar_sem_requisicao_e_com_anonimo():
    evento = registrar(TipoEvento.LOGIN_FALHA, usuario=AnonymousUser(), email_informado="x" * 300)
    assert evento.usuario is None
    assert evento.ip is None
    assert evento.agente == ""
    assert len(evento.email_informado) == 254


def test_ip_invalido_nao_e_gravado(rf):
    evento = registrar(TipoEvento.LOGOUT, request=_requisicao(rf, ip="nao-e-ip"))
    assert evento.ip is None


def test_evento_nao_pode_ser_alterado_nem_apagado_pelo_django():
    evento = registrar(TipoEvento.LOGOUT)
    evento.tipo = TipoEvento.LOGIN_SUCESSO
    with pytest.raises(EventoImutavelError):
        evento.save()
    with pytest.raises(EventoImutavelError):
        evento.delete()
    with pytest.raises(EventoImutavelError):
        EventoAuditoria.objects.filter(pk=evento.pk).update(tipo=TipoEvento.LOGIN_SUCESSO)
    with pytest.raises(EventoImutavelError):
        EventoAuditoria.objects.filter(pk=evento.pk).delete()


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE auditoria_eventoauditoria SET tipo = 'LOGIN_SUCESSO' WHERE id = %s",
        "DELETE FROM auditoria_eventoauditoria WHERE id = %s",
    ],
    ids=["update", "delete"],
)
def test_gatilho_do_banco_barra_alteracao_direta(sql):
    evento = registrar(TipoEvento.LOGOUT)
    with (
        pytest.raises(DatabaseError, match="nao podem ser alterados"),
        transaction.atomic(),
        connection.cursor() as cursor,
    ):
        cursor.execute(sql, [evento.pk])
    evento.refresh_from_db()
    assert evento.tipo == TipoEvento.LOGOUT


def test_login_e_logout_geram_eventos(client):
    professor = ProfessorFactory()
    client.force_login(professor)
    client.logout()
    tipos = list(
        EventoAuditoria.objects.filter(usuario=professor).order_by("id").values_list("tipo", flat=True)
    )
    assert tipos == [TipoEvento.LOGIN_SUCESSO, TipoEvento.LOGOUT]


def test_falha_de_login_registra_o_email_digitado_e_nunca_a_senha(rf):
    ProfessorFactory(email="carla@ifpb.edu.br")
    assert authenticate(_requisicao(rf), username="carla@ifpb.edu.br", password="senha-errada") is None
    evento = EventoAuditoria.objects.get(tipo=TipoEvento.LOGIN_FALHA)
    assert evento.email_informado == "carla@ifpb.edu.br"
    assert evento.usuario is None
    assert evento.ip == "10.0.0.7"
    assert evento.detalhes == {"conta_bloqueada": False}
    assert "senha-errada" not in str(evento.detalhes)


def test_usuario_desativado_nao_entra(rf):
    ProfessorFactory(email="inativo@ifpb.edu.br", is_active=False)
    assert authenticate(_requisicao(rf), username="inativo@ifpb.edu.br", password=SENHA_PADRAO) is None
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.LOGIN_FALHA).count() == 1
