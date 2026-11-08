"""Serviços dos cadastros (IDs 16 e 17): permissões por perfil e curso, auditoria e exclusão protegida."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.academico import servicos
from apps.academico.models import CoordenacaoCurso, Curso, Turma
from apps.auditoria.models import EventoAuditoria, TipoEvento
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


@pytest.fixture
def curso():
    return CursoFactory(codigo="661", nome="Técnico em Informática")


@pytest.fixture
def coordenador(curso):
    usuario = CoordenadorFactory()
    CoordenacaoCurso.objects.create(curso=curso, usuario=usuario)
    return usuario


def _dados_turma(curso, identificador="1º A"):
    return {"curso": curso, "ano_letivo": 2026, "serie": 1, "identificador": identificador}


def test_admin_cria_e_altera_curso_com_auditoria():
    admin = AdminFactory()
    curso = servicos.salvar_curso(por=admin, dados={"codigo": "700", "nome": "Técnico em Edificações"})
    servicos.salvar_curso(
        por=admin, curso=curso, dados={"codigo": "700", "nome": "Técnico em Edificações Integrado"}
    )
    servicos.salvar_curso(
        por=admin, curso=curso, dados={"codigo": "700", "nome": "Técnico em Edificações Integrado"}
    )
    criado = EventoAuditoria.objects.get(tipo=TipoEvento.CADASTRO_CRIADO)
    assert criado.detalhes == {"valores": {"codigo": "700", "nome": "Técnico em Edificações"}}
    alterado = EventoAuditoria.objects.get(tipo=TipoEvento.CADASTRO_ALTERADO)  # o 2º salvar não mudou nada
    assert alterado.detalhes["mudancas"] == {
        "nome": {"antes": "Técnico em Edificações", "depois": "Técnico em Edificações Integrado"}
    }


@pytest.mark.parametrize("fabrica", [CoordenadorFactory, ProfessorFactory])
def test_so_admin_cadastra_curso_e_coordenadores(fabrica, curso):
    usuario = fabrica()
    with pytest.raises(PermissionDenied):
        servicos.salvar_curso(por=usuario, dados={"codigo": "1", "nome": "X"})
    with pytest.raises(PermissionDenied):
        servicos.vincular_coordenador(por=usuario, curso=curso, usuario=CoordenadorFactory())


def test_vincular_e_desvincular_coordenador(curso):
    admin, coordenador = AdminFactory(), CoordenadorFactory()
    servicos.vincular_coordenador(por=admin, curso=curso, usuario=coordenador)
    assert list(curso.coordenadores.all()) == [coordenador]
    with pytest.raises(ValidationError):
        servicos.vincular_coordenador(por=admin, curso=curso, usuario=ProfessorFactory())
    servicos.desvincular_coordenador(por=admin, curso=curso, usuario=coordenador)
    servicos.desvincular_coordenador(por=admin, curso=curso, usuario=coordenador)  # repetir: sem evento
    assert not curso.coordenadores.exists()
    tipos = list(EventoAuditoria.objects.order_by("id").values_list("tipo", flat=True))
    assert tipos == [TipoEvento.COORDENACAO_ADICIONADA, TipoEvento.COORDENACAO_REMOVIDA]


def test_coordenador_cadastra_turma_e_disciplina_so_no_proprio_curso(curso, coordenador):
    turma = servicos.salvar_turma(por=coordenador, dados=_dados_turma(curso))
    disciplina = servicos.salvar_disciplina(
        por=coordenador, dados={"curso": curso, "codigo": "TIN.0001", "nome": "Lógica", "optativa": False}
    )
    assert (turma.curso, disciplina.curso) == (curso, curso)
    outro_curso = CursoFactory()
    with pytest.raises(PermissionDenied):
        servicos.salvar_turma(por=coordenador, dados=_dados_turma(outro_curso))
    with pytest.raises(PermissionDenied):  # nem mover a própria turma para outro curso
        servicos.salvar_turma(por=coordenador, turma=turma, dados={"curso": outro_curso})
    turma_alheia = TurmaFactory(curso=outro_curso)
    with pytest.raises(PermissionDenied):  # nem trazer turma alheia para o próprio curso
        servicos.salvar_turma(por=coordenador, turma=turma_alheia, dados={"curso": curso})
    turma.refresh_from_db()
    assert turma.curso == curso


def test_professor_nao_cadastra_nada():
    professor = ProfessorFactory()
    curso = CursoFactory()
    with pytest.raises(PermissionDenied):
        servicos.salvar_turma(por=professor, dados=_dados_turma(curso))
    with pytest.raises(PermissionDenied):
        servicos.salvar_disciplina(por=professor, dados={"curso": curso, "codigo": "X", "nome": "X"})
    with pytest.raises(PermissionDenied):
        servicos.salvar_turma(por=professor, dados={"ano_letivo": 2026, "identificador": "sem curso"})


def test_validacao_do_modelo_vale_nos_servicos(curso, coordenador):
    servicos.salvar_turma(por=coordenador, dados=_dados_turma(curso))
    with pytest.raises(ValidationError):
        servicos.salvar_turma(por=coordenador, dados=_dados_turma(curso))  # repetida
    assert Turma.objects.count() == 1


def test_diario_vincula_turma_e_troca_professor_com_auditoria(curso, coordenador):
    diario = DiarioFactory(disciplina=DisciplinaFactory(curso=curso))
    turma = TurmaFactory(curso=curso, ano_letivo=diario.ano_letivo)
    novo_professor = ProfessorFactory(nome="Novo Professor")
    servicos.salvar_diario(
        por=coordenador, diario=diario, dados={"turma": turma, "professor": novo_professor}
    )
    diario.refresh_from_db()
    assert (diario.turma, diario.professor) == (turma, novo_professor)
    mudancas = EventoAuditoria.objects.get(tipo=TipoEvento.CADASTRO_ALTERADO).detalhes["mudancas"]
    assert set(mudancas) == {"turma", "professor"}
    assert mudancas["professor"]["depois"] == str(novo_professor)
    with pytest.raises(PermissionDenied):
        servicos.salvar_diario(por=diario.professor, diario=diario, dados={"turma": None})


def test_exclusao_so_quando_nao_ha_vinculos(curso, coordenador):
    turma = servicos.salvar_turma(por=coordenador, dados=_dados_turma(curso))
    diario = DiarioFactory(disciplina=DisciplinaFactory(curso=curso), turma=turma, ano_letivo=2026)
    with pytest.raises(ValidationError) as erro:
        servicos.excluir_turma(por=coordenador, turma=turma)
    assert erro.value.code == "em_uso"
    with pytest.raises(ValidationError):
        servicos.excluir_disciplina(por=coordenador, disciplina=diario.disciplina)
    servicos.salvar_diario(por=coordenador, diario=diario, dados={"turma": None})
    servicos.excluir_turma(por=coordenador, turma=turma)
    assert not Turma.objects.exists()
    excluido = EventoAuditoria.objects.get(tipo=TipoEvento.CADASTRO_EXCLUIDO)
    assert (excluido.objeto_tipo, excluido.detalhes["valores"]["identificador"]) == (
        "academico.Turma",
        "1º A",
    )
    servicos.excluir_diario(por=coordenador, diario=diario)
    servicos.excluir_disciplina(por=coordenador, disciplina=diario.disciplina)


def test_curso_em_uso_nao_e_excluido_e_vazio_sim(curso):
    admin = AdminFactory()
    TurmaFactory(curso=curso)
    with pytest.raises(ValidationError):
        servicos.excluir_curso(por=admin, curso=curso)
    vazio = CursoFactory()
    servicos.excluir_curso(por=admin, curso=vazio)
    assert not Curso.objects.filter(pk=vazio.pk).exists()


def test_coordenador_nao_exclui_em_curso_alheio(coordenador):
    turma = TurmaFactory()
    with pytest.raises(PermissionDenied):
        servicos.excluir_turma(por=coordenador, turma=turma)
    assert Turma.objects.filter(pk=turma.pk).exists()


def test_admin_cadastra_em_qualquer_curso():
    admin = AdminFactory()
    turma = servicos.salvar_turma(por=admin, dados=_dados_turma(CursoFactory()))
    assert turma.pk is not None
