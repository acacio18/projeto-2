"""Fábricas de dados para os testes (factory_boy)."""

import factory

from apps.contas.models import Perfil, Usuario

SENHA_PADRAO = "senha-de-teste-123"


class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuario
        skip_postgeneration_save = True

    nome = factory.Sequence(lambda n: f"Pessoa de Teste {n}")
    email = factory.Sequence(lambda n: f"pessoa{n}@ifpb.edu.br")
    perfil = Perfil.PROFESSOR
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):  # noqa: N805 (convenção do factory_boy)
        obj.set_password(extracted or SENHA_PADRAO)
        if create:
            obj.save(update_fields=["password"])


class ProfessorFactory(UsuarioFactory):
    perfil = Perfil.PROFESSOR


class CoordenadorFactory(UsuarioFactory):
    perfil = Perfil.COORDENADOR


class AdminFactory(UsuarioFactory):
    perfil = Perfil.ADMIN
