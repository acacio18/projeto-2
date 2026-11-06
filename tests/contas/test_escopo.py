"""Política central de escopo (ID 2): matriz perfil × o que cada um vê e pode fazer."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404

from apps.contas import escopo
from apps.contas.models import Perfil
from tests.apoio.fabricas import AdminFactory, CoordenadorFactory, ProfessorFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def pessoas():
    return {
        "admin": AdminFactory(),
        "coordenador": CoordenadorFactory(),
        "professor": ProfessorFactory(),
        "outro_professor": ProfessorFactory(),
    }


def test_admin_ve_todos_os_usuarios(pessoas):
    assert set(escopo.usuarios_visiveis(pessoas["admin"])) == set(pessoas.values())


@pytest.mark.parametrize("quem", ["coordenador", "professor"])
def test_quem_nao_e_admin_ve_so_o_proprio_cadastro(pessoas, quem):
    assert list(escopo.usuarios_visiveis(pessoas[quem])) == [pessoas[quem]]


@pytest.mark.parametrize(("quem", "pode"), [("admin", True), ("coordenador", False), ("professor", False)])
def test_so_admin_gerencia_usuarios(pessoas, quem, pode):
    assert escopo.pode_gerenciar_usuarios(pessoas[quem]) is pode


def test_admin_desativado_perde_tudo(pessoas):
    admin = pessoas["admin"]
    admin.is_active = False
    assert not escopo.pode_gerenciar_usuarios(admin)
    assert list(escopo.usuarios_visiveis(admin)) == []


def test_anonimo_nao_ve_nada():
    anonimo = AnonymousUser()
    assert not escopo.esta_ativo(anonimo)
    assert not escopo.esta_ativo(None)
    assert list(escopo.usuarios_visiveis(anonimo)) == []
    with pytest.raises(PermissionDenied):
        escopo.exigir_perfil(anonimo, Perfil.ADMIN)


@pytest.mark.parametrize(
    ("quem", "perfis", "barra"),
    [
        ("admin", (Perfil.ADMIN,), False),
        ("coordenador", (Perfil.ADMIN,), True),
        ("coordenador", (Perfil.ADMIN, Perfil.COORDENADOR), False),
        ("professor", (Perfil.ADMIN, Perfil.COORDENADOR), True),
    ],
)
def test_exigir_perfil(pessoas, quem, perfis, barra):
    if barra:
        with pytest.raises(PermissionDenied):
            escopo.exigir_perfil(pessoas[quem], *perfis)
    else:
        escopo.exigir_perfil(pessoas[quem], *perfis)


def test_registro_fora_do_escopo_responde_404_sem_revelar_que_existe(pessoas):
    professor, outro = pessoas["professor"], pessoas["outro_professor"]
    assert escopo.obter_usuario_visivel(professor, professor.pk) == professor
    with pytest.raises(Http404):
        escopo.obter_usuario_visivel(professor, outro.pk)
    with pytest.raises(Http404):
        escopo.obter_usuario_visivel(pessoas["admin"], 999_999)
