"""Modelo de usuário: e-mail institucional como login, perfis e criação pelo manage.py."""

import pytest
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.db import IntegrityError, transaction

from apps.contas.models import Perfil, Usuario
from apps.contas.validadores import validar_email_institucional
from tests.apoio.fabricas import AdminFactory, CoordenadorFactory, ProfessorFactory

pytestmark = pytest.mark.django_db


def test_create_user_normaliza_email_e_comeca_como_professor_sem_senha():
    usuario = Usuario.objects.create_user(email="  Maria.Silva@IFPB.edu.br ", nome="Maria Silva")
    assert usuario.email == "maria.silva@ifpb.edu.br"
    assert usuario.perfil == Perfil.PROFESSOR
    assert not usuario.is_staff
    assert not usuario.is_superuser
    assert not usuario.has_usable_password()


def test_create_superuser_e_administrador():
    usuario = Usuario.objects.create_superuser(email="admin@ifpb.edu.br", nome="Admin", password="x" * 12)
    assert usuario.perfil == Perfil.ADMIN
    assert usuario.is_staff
    assert usuario.is_superuser
    assert usuario.check_password("x" * 12)


def test_email_e_obrigatorio():
    with pytest.raises(ValueError, match="obrigatório"):
        Usuario.objects.create_user(email="", nome="Sem E-mail")


@pytest.mark.parametrize("email", ["prof@ifpb.edu.br", "Prof.Nome@IFPB.EDU.BR"])
def test_aceita_email_do_dominio_institucional(email):
    validar_email_institucional(email)


@pytest.mark.parametrize(
    "email",
    [
        "prof@gmail.com",
        "aluno@academico.ifpb.edu.br",  # subdomínio: não aceito sem configuração explícita
        "prof@ifpb.edu.br.exemplo.com",
        "prof@xifpb.edu.br",
        "sem-arroba",
    ],
)
def test_recusa_email_fora_do_dominio_institucional(email):
    with pytest.raises(ValidationError) as erro:
        validar_email_institucional(email)
    assert erro.value.code == "email_nao_institucional"
    assert "@ifpb.edu.br" in erro.value.messages[0]


def test_dominios_vem_da_configuracao(settings):
    settings.CONTAS_DOMINIOS_EMAIL = ["ifpb.edu.br", "@academico.ifpb.edu.br"]
    validar_email_institucional("aluno@academico.ifpb.edu.br")


def test_email_e_unico_sem_diferenciar_maiusculas():
    ProfessorFactory(email="repetido@ifpb.edu.br")
    outro = Usuario(email="REPETIDO@ifpb.edu.br", nome="Outro", password="!")
    with pytest.raises(ValidationError) as erro:
        outro.full_clean()
    assert erro.value.message_dict["email"] == ["Já existe um usuário com este e-mail."]
    with pytest.raises(IntegrityError), transaction.atomic():
        Usuario.objects.create_user(email="Repetido@IFPB.edu.br", nome="Outro")


def test_login_encontra_o_usuario_sem_diferenciar_maiusculas():
    professor = ProfessorFactory(email="joana@ifpb.edu.br")
    assert Usuario.objects.get_by_natural_key("JOANA@ifpb.edu.br") == professor


def test_perfis_e_nomes():
    admin, coordenador, professor = (
        AdminFactory(),
        CoordenadorFactory(),
        ProfessorFactory(nome="Ana Maria Souza"),
    )
    assert (admin.eh_admin, admin.eh_coordenador, admin.eh_professor) == (True, False, False)
    assert (coordenador.eh_admin, coordenador.eh_coordenador, coordenador.eh_professor) == (
        False,
        True,
        False,
    )
    assert (professor.eh_admin, professor.eh_coordenador, professor.eh_professor) == (False, False, True)
    assert professor.get_full_name() == "Ana Maria Souza"
    assert professor.get_short_name() == "Ana"
    assert str(professor) == f"Ana Maria Souza <{professor.email}>"
    assert Usuario(email="x@ifpb.edu.br", nome="").get_short_name() == "x@ifpb.edu.br"


def test_createsuperuser_pelo_manage_py(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "senha-forte-do-admin")
    call_command(
        "createsuperuser", interactive=False, email="Diretor@ifpb.edu.br", nome="Diretor", verbosity=0
    )
    admin = Usuario.objects.get(email="diretor@ifpb.edu.br")
    assert admin.perfil == Perfil.ADMIN
    assert admin.check_password("senha-forte-do-admin")


def test_createsuperuser_recusa_email_nao_institucional(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "senha-forte-do-admin")
    with pytest.raises(CommandError, match="institucional"):
        call_command("createsuperuser", interactive=False, email="admin@gmail.com", nome="Admin", verbosity=0)
