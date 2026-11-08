"""Escopo de dados acadêmicos (ID 2): quem vê quais cursos, turmas, disciplinas, diários e professores.

Critério de aceitação da E1 que dependia dos diários: um professor não acessa diário alheio.
"""

import pytest
from django.http import Http404

from apps.academico.models import CoordenacaoCurso
from apps.contas import escopo
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
def cenario():
    informatica, edificacoes = CursoFactory(nome="Informática"), CursoFactory(nome="Edificações")
    coordenadora = CoordenadorFactory(nome="Coordenadora de Informática")
    CoordenacaoCurso.objects.create(curso=informatica, usuario=coordenadora)
    ana, beto = ProfessorFactory(nome="Ana"), ProfessorFactory(nome="Beto")
    turma_info = TurmaFactory(curso=informatica)
    diario_ana = DiarioFactory(disciplina=DisciplinaFactory(curso=informatica), professor=ana)
    diario_beto = DiarioFactory(disciplina=DisciplinaFactory(curso=edificacoes), professor=beto)
    # a coordenadora também dá aula em Edificações
    diario_coord = DiarioFactory(disciplina=DisciplinaFactory(curso=edificacoes), professor=coordenadora)
    return locals()


def _pks(consulta):
    return set(consulta.values_list("pk", flat=True))


def test_professor_ve_so_os_proprios_diarios_e_o_que_vem_deles(cenario):
    ana = cenario["ana"]
    assert _pks(escopo.diarios_visiveis(ana)) == {cenario["diario_ana"].pk}
    assert _pks(escopo.cursos_visiveis(ana)) == {cenario["informatica"].pk}
    assert _pks(escopo.disciplinas_visiveis(ana)) == {cenario["diario_ana"].disciplina_id}
    assert _pks(escopo.turmas_visiveis(ana)) == set()  # o diário dela ainda não tem turma
    assert not escopo.cursos_gerenciaveis(ana).exists()
    assert not escopo.diarios_gerenciaveis(ana).exists()


def test_professor_nao_acessa_diario_alheio_nem_pelo_id(cenario):
    with pytest.raises(Http404):
        escopo.obter_visivel(escopo.diarios_visiveis(cenario["ana"]), cenario["diario_beto"].pk)


def test_coordenador_ve_o_curso_que_coordena_e_os_proprios_diarios(cenario):
    coord = cenario["coordenadora"]
    assert _pks(escopo.diarios_visiveis(coord)) == {cenario["diario_ana"].pk, cenario["diario_coord"].pk}
    assert _pks(escopo.diarios_gerenciaveis(coord)) == {cenario["diario_ana"].pk}  # só gerencia Informática
    assert _pks(escopo.cursos_gerenciaveis(coord)) == {cenario["informatica"].pk}
    assert _pks(escopo.cursos_visiveis(coord)) == {cenario["informatica"].pk, cenario["edificacoes"].pk}
    assert cenario["turma_info"].pk in _pks(escopo.turmas_visiveis(coord))
    assert escopo.pode_gerenciar_curso(coord, cenario["informatica"])
    assert not escopo.pode_gerenciar_curso(coord, cenario["edificacoes"])
    assert not escopo.pode_cadastrar_cursos(coord)


def test_coordenador_ve_os_professores_do_curso(cenario):
    coord = cenario["coordenadora"]
    assert _pks(escopo.usuarios_visiveis(coord)) == {coord.pk, cenario["ana"].pk}  # Beto é de outro curso
    assert list(escopo.professores_do_curso(cenario["informatica"])) == [cenario["ana"]]


def test_admin_ve_tudo(cenario):
    admin = AdminFactory()
    assert escopo.diarios_visiveis(admin).count() == 3
    assert escopo.cursos_visiveis(admin).count() == 2
    assert escopo.turmas_visiveis(admin).count() == 1
    assert escopo.disciplinas_visiveis(admin).count() == 3
    assert escopo.pode_cadastrar_cursos(admin)


def test_inativo_e_anonimo_nao_veem_nada(cenario):
    from django.contrib.auth.models import AnonymousUser

    inativa = cenario["ana"]
    inativa.is_active = False
    for usuario in (inativa, AnonymousUser()):
        for consulta in (escopo.diarios_visiveis, escopo.cursos_visiveis, escopo.turmas_visiveis):
            assert not consulta(usuario).exists()
        assert not escopo.disciplinas_visiveis(usuario).exists()


def test_listas_para_vincular(cenario):
    ProfessorFactory(is_active=False)
    AdminFactory()
    atribuiveis = set(escopo.professores_atribuiveis())
    assert atribuiveis == {cenario["ana"], cenario["beto"], cenario["coordenadora"]}
    assert list(escopo.coordenadores_disponiveis()) == [cenario["coordenadora"]]


def test_inativo_ve_nenhum_usuario(cenario):
    inativa = cenario["ana"]
    inativa.is_active = False
    assert not escopo.usuarios_visiveis(inativa).exists()
    assert not escopo.cursos_gerenciaveis(inativa).exists()
