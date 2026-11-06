"""Serviços do cadastro de usuários (ID 15): regras e auditoria."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404

from apps.auditoria.models import EventoAuditoria, TipoEvento
from apps.contas import servicos
from apps.contas.models import Perfil
from tests.apoio.fabricas import AdminFactory, CoordenadorFactory, ProfessorFactory

pytestmark = pytest.mark.django_db


def _eventos(tipo):
    return EventoAuditoria.objects.filter(tipo=tipo)


def test_admin_cria_usuario_sem_senha_e_auditado(rf):
    admin = AdminFactory()
    novo = servicos.criar_usuario(
        por=admin,
        nome="  Paulo Lima ",
        email="Paulo.Lima@IFPB.edu.br",
        perfil=Perfil.COORDENADOR,
        request=rf.post("/", REMOTE_ADDR="10.1.1.1"),
    )
    assert (novo.nome, novo.email, novo.perfil, novo.is_active) == (
        "Paulo Lima",
        "paulo.lima@ifpb.edu.br",
        Perfil.COORDENADOR,
        True,
    )
    assert not novo.has_usable_password()
    evento = _eventos(TipoEvento.USUARIO_CRIADO).get()
    assert (evento.usuario, evento.objeto_id, evento.ip) == (admin, str(novo.pk), "10.1.1.1")
    assert evento.detalhes == {"perfil": Perfil.COORDENADOR}


@pytest.mark.parametrize("fabrica", [CoordenadorFactory, ProfessorFactory])
def test_quem_nao_e_admin_nao_cria(fabrica):
    with pytest.raises(PermissionDenied):
        servicos.criar_usuario(por=fabrica(), nome="X", email="x@ifpb.edu.br", perfil=Perfil.PROFESSOR)
    assert not _eventos(TipoEvento.USUARIO_CRIADO).exists()


@pytest.mark.parametrize(("email", "campo"), [("x@gmail.com", "email"), ("existente@ifpb.edu.br", "email")])
def test_criacao_valida_dominio_e_duplicidade(email, campo):
    admin = AdminFactory()
    ProfessorFactory(email="existente@ifpb.edu.br")
    with pytest.raises(ValidationError) as erro:
        servicos.criar_usuario(por=admin, nome="X", email=email.upper(), perfil=Perfil.PROFESSOR)
    assert campo in erro.value.message_dict


def test_alteracao_registra_antes_e_depois_so_do_que_mudou():
    admin = AdminFactory()
    alvo = ProfessorFactory(nome="Nome Antigo", email="antigo@ifpb.edu.br")
    servicos.alterar_usuario(
        por=admin, alvo=alvo, nome="Nome Novo", email="antigo@ifpb.edu.br", perfil=Perfil.COORDENADOR
    )
    alvo.refresh_from_db()
    assert (alvo.nome, alvo.perfil) == ("Nome Novo", Perfil.COORDENADOR)
    assert _eventos(TipoEvento.USUARIO_ALTERADO).get().detalhes == {
        "mudancas": {
            "nome": {"antes": "Nome Antigo", "depois": "Nome Novo"},
            "perfil": {"antes": Perfil.PROFESSOR, "depois": Perfil.COORDENADOR},
        }
    }


def test_alteracao_sem_mudanca_nao_gera_evento():
    admin, alvo = AdminFactory(), ProfessorFactory()
    servicos.alterar_usuario(
        por=admin, alvo=alvo, nome=alvo.nome, email=alvo.email.upper(), perfil=alvo.perfil
    )
    assert not _eventos(TipoEvento.USUARIO_ALTERADO).exists()


def test_alteracao_por_quem_nao_e_admin_e_barrada():
    coordenador, alvo = CoordenadorFactory(), ProfessorFactory()
    with pytest.raises(PermissionDenied):
        servicos.alterar_usuario(por=coordenador, alvo=alvo, nome="X", email=alvo.email, perfil=Perfil.ADMIN)


def test_nao_rebaixa_o_ultimo_admin_ativo():
    admin = AdminFactory()
    AdminFactory(is_active=False)  # admin desativado não conta
    with pytest.raises(ValidationError) as erro:
        servicos.alterar_usuario(
            por=admin, alvo=admin, nome=admin.nome, email=admin.email, perfil=Perfil.PROFESSOR
        )
    assert erro.value.code == "ultimo_admin"


def test_rebaixa_admin_quando_existe_outro_ativo():
    admin, outro = AdminFactory(), AdminFactory()
    servicos.alterar_usuario(
        por=admin, alvo=outro, nome=outro.nome, email=outro.email, perfil=Perfil.PROFESSOR
    )
    outro.refresh_from_db()
    assert outro.perfil == Perfil.PROFESSOR


def test_desativa_e_reativa_com_auditoria():
    admin, alvo = AdminFactory(), ProfessorFactory()
    servicos.desativar_usuario(por=admin, alvo=alvo)
    alvo.refresh_from_db()
    assert not alvo.is_active
    servicos.desativar_usuario(por=admin, alvo=alvo)  # repetir não gera outro evento
    servicos.reativar_usuario(por=admin, alvo=alvo)
    servicos.reativar_usuario(por=admin, alvo=alvo)
    alvo.refresh_from_db()
    assert alvo.is_active
    assert _eventos(TipoEvento.USUARIO_DESATIVADO).count() == 1
    assert _eventos(TipoEvento.USUARIO_REATIVADO).count() == 1


def test_ninguem_desativa_a_si_mesmo():
    admin = AdminFactory()
    AdminFactory()
    with pytest.raises(ValidationError) as erro:
        servicos.desativar_usuario(por=admin, alvo=admin)
    assert erro.value.code == "desativar_a_si_mesmo"


def test_admin_desativado_perde_o_poder_de_desativar():
    admin, outro_admin = AdminFactory(), AdminFactory()
    servicos.desativar_usuario(por=admin, alvo=outro_admin)
    outro_admin.refresh_from_db()
    with pytest.raises(PermissionDenied):
        servicos.desativar_usuario(por=outro_admin, alvo=admin)
    admin.refresh_from_db()
    assert admin.is_active


@pytest.mark.parametrize("operacao", [servicos.desativar_usuario, servicos.reativar_usuario])
def test_operacoes_de_status_exigem_admin(operacao):
    with pytest.raises(PermissionDenied):
        operacao(por=ProfessorFactory(), alvo=ProfessorFactory())


def test_alvo_inexistente_responde_404():
    admin = AdminFactory()
    fantasma = ProfessorFactory.build(pk=987_654)
    with pytest.raises(Http404):
        servicos.desativar_usuario(por=admin, alvo=fantasma)
