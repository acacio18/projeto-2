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


# --- Cadastros acadêmicos (E2) -----------------------------------------------------------------


class CursoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "academico.Curso"

    codigo = factory.Sequence(lambda n: str(600 + n))
    nome = factory.Sequence(lambda n: f"Técnico em Curso {n} Integrado ao Ensino Médio")


class TurmaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "academico.Turma"

    curso = factory.SubFactory(CursoFactory)
    ano_letivo = 2026
    serie = 1
    identificador = factory.Sequence(lambda n: f"Turma {n}")


class DisciplinaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "academico.Disciplina"

    curso = factory.SubFactory(CursoFactory)
    codigo = factory.Sequence(lambda n: f"TST.{n:04d}")
    nome = factory.Sequence(lambda n: f"Disciplina {n}")
    carga_horaria_horas = 67


class DiarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "academico.Diario"

    codigo = factory.Sequence(lambda n: str(80000 + n))
    disciplina = factory.SubFactory(DisciplinaFactory)
    curso = factory.SelfAttribute("disciplina.curso")
    professor = factory.SubFactory(ProfessorFactory)
    ano_letivo = 2026
    periodo_letivo = 1
    aulas_previstas = 80
