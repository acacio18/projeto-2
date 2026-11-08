"""Restrições dos cadastros acadêmicos (unicidade, faixas válidas e coerência entre curso, turma e diário)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.academico.models import CoordenacaoCurso, Diario, Estudante, Turma
from tests.apoio.fabricas import (
    AdminFactory,
    CoordenadorFactory,
    CursoFactory,
    DiarioFactory,
    DisciplinaFactory,
    ProfessorFactory,
    TurmaFactory,
)

pytestmark = pytest.mark.django_db


def _viola_no_banco(**campos):
    with pytest.raises(IntegrityError), transaction.atomic():
        Turma.objects.create(**campos)


def test_turma_unica_por_curso_ano_e_identificacao():
    turma = TurmaFactory(identificador="3º A")
    _viola_no_banco(curso=turma.curso, ano_letivo=turma.ano_letivo, identificador="3º A")
    TurmaFactory(curso=turma.curso, ano_letivo=turma.ano_letivo + 1, identificador="3º A")  # outro ano: ok


@pytest.mark.parametrize(("ano", "serie"), [(1999, 1), (2101, 1), (2026, 0), (2026, 5)])
def test_turma_recusa_ano_e_serie_fora_da_faixa(ano, serie):
    curso = CursoFactory()
    _viola_no_banco(curso=curso, ano_letivo=ano, serie=serie, identificador="X")
    with pytest.raises(ValidationError):
        Turma(curso=curso, ano_letivo=ano, serie=serie, identificador="X").full_clean()


def test_disciplina_e_diario_unicos_pelos_codigos_do_suap():
    disciplina = DisciplinaFactory(codigo="TIN.0054")
    with pytest.raises(IntegrityError), transaction.atomic():
        DisciplinaFactory(curso=disciplina.curso, codigo="TIN.0054")
    DisciplinaFactory(codigo="TIN.0054")  # mesmo código em outro curso: ok
    diario = DiarioFactory(codigo="70764", ano_letivo=2023)
    with pytest.raises(IntegrityError), transaction.atomic():
        DiarioFactory(codigo="70764", ano_letivo=2023)
    DiarioFactory(codigo="70764", ano_letivo=2024)  # outro ano: ok
    assert str(diario).startswith("70764 - ")


def test_diario_coerente_com_curso_turma_ano_e_professor():
    diario = DiarioFactory(ano_letivo=2026)
    diario.full_clean()
    diario.disciplina = DisciplinaFactory()  # de outro curso
    diario.turma = TurmaFactory(ano_letivo=2025)  # outro curso e outro ano
    diario.professor = AdminFactory()  # administrador não é professor de diário
    with pytest.raises(ValidationError) as erro:
        diario.full_clean()
    assert set(erro.value.message_dict) == {"disciplina", "turma", "professor"}


def test_turma_do_mesmo_curso_mas_de_outro_ano_e_recusada():
    diario = DiarioFactory(ano_letivo=2026)
    diario.turma = TurmaFactory(curso=diario.curso, ano_letivo=2025)
    with pytest.raises(ValidationError) as erro:
        diario.full_clean()
    assert "mesmo ano letivo" in erro.value.message_dict["turma"][0]


def test_professor_inativo_nao_pode_ser_responsavel():
    diario = DiarioFactory()
    diario.professor = ProfessorFactory(is_active=False)
    with pytest.raises(ValidationError):
        diario.full_clean()
    diario.professor = CoordenadorFactory()  # coordenador que dá aula: ok
    diario.full_clean()


def test_so_coordenador_coordena_curso():
    curso = CursoFactory()
    with pytest.raises(ValidationError):
        CoordenacaoCurso(curso=curso, usuario=ProfessorFactory()).full_clean()
    vinculo = CoordenacaoCurso.objects.create(curso=curso, usuario=CoordenadorFactory(nome="Clara Nunes"))
    vinculo.full_clean()
    assert str(vinculo) == f"Clara Nunes coordena {curso.nome}"
    with pytest.raises(IntegrityError), transaction.atomic():
        CoordenacaoCurso.objects.create(curso=curso, usuario=vinculo.usuario)


@pytest.mark.parametrize(
    ("matricula", "valida"), [("201927621032", True), ("2019276210", False), ("20192762103A", False)]
)
def test_formato_da_matricula(matricula, valida, settings):
    estudante = Estudante(matricula=matricula, nome="Fulano")
    if valida:
        estudante.full_clean()
    else:
        with pytest.raises(ValidationError):
            estudante.full_clean()
    settings.ACADEMICO_MATRICULA_REGEX = r"^\d{10}$"
    Estudante(matricula="2019276210", nome="Outro formato").full_clean()


def test_textos_dos_cadastros():
    turma = TurmaFactory(identificador="2º B", ano_letivo=2026)
    assert str(turma) == "2º B (2026)"
    assert str(turma.curso).startswith(turma.curso.codigo)
    disciplina = DisciplinaFactory(codigo="TIN.0001", nome="Lógica")
    assert str(disciplina) == "TIN.0001 - Lógica"
    estudante = Estudante.objects.create(matricula="201927621032", nome="Ana")
    diario = DiarioFactory()
    matricula = estudante.matriculas.create(diario=diario)
    assert str(estudante) == "Ana (201927621032)"
    assert str(matricula) == f"Ana (201927621032) em {diario.codigo}"
    assert Diario.objects.get(pk=diario.pk).turma is None
