"""Casos de uso dos cadastros acadêmicos (IDs 16 e 17). As telas só chamam estas funções.

Regras de permissão (apps/contas/escopo.py):
- cursos e coordenadores: só o Administrador;
- turmas, disciplinas e diários: Administrador, ou Coordenador nos cursos que coordena;
- toda criação, alteração e exclusão gera evento de auditoria com o antes e o depois (ID 13).
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.db.models import ProtectedError

from apps.academico.models import CoordenacaoCurso, Curso, Diario, Disciplina, Turma
from apps.auditoria.models import TipoEvento
from apps.auditoria.registro import registrar
from apps.contas import escopo

CAMPOS = {
    Curso: ["codigo", "nome"],
    Turma: ["curso", "ano_letivo", "serie", "identificador"],
    Disciplina: ["curso", "codigo", "nome", "carga_horaria_horas", "optativa"],
    Diario: [
        "codigo",
        "curso",
        "disciplina",
        "turma",
        "professor",
        "ano_letivo",
        "periodo_letivo",
        "aulas_previstas",
        "carga_horaria_horas",
    ],
}


def _valor_auditavel(valor):
    if isinstance(valor, models.Model):
        return str(valor)
    return valor


def _instantaneo(instancia) -> dict:
    return {campo: _valor_auditavel(getattr(instancia, campo)) for campo in CAMPOS[type(instancia)]}


def _exigir_curso_gerenciavel(por, curso) -> None:
    if curso is None or not escopo.pode_gerenciar_curso(por, curso):
        raise PermissionDenied


@transaction.atomic
def _salvar(*, por, instancia, dados: dict, request, verificar) -> models.Model:
    """Cria ou altera `instancia` com `dados`, depois de `verificar` a permissão no antes e no depois."""
    nova = instancia.pk is None
    if not nova:
        verificar(instancia)
    antes = {} if nova else _instantaneo(instancia)
    for campo, valor in dados.items():
        setattr(instancia, campo, valor)
    verificar(instancia)
    instancia.full_clean()
    depois = _instantaneo(instancia)
    if nova:
        instancia.save()
        registrar(TipoEvento.CADASTRO_CRIADO, request=request, usuario=por, objeto=instancia, valores=depois)
        return instancia
    mudancas = {c: {"antes": antes[c], "depois": depois[c]} for c in depois if antes[c] != depois[c]}
    if mudancas:
        instancia.save()
        registrar(
            TipoEvento.CADASTRO_ALTERADO, request=request, usuario=por, objeto=instancia, mudancas=mudancas
        )
    return instancia


@transaction.atomic
def _excluir(*, por, instancia, request, verificar, motivo_bloqueio: str) -> None:
    verificar(instancia)
    valores = _instantaneo(instancia)
    rotulo, pk = instancia._meta.label, instancia.pk
    try:
        with transaction.atomic():
            instancia.delete()
    except ProtectedError as erro:
        raise ValidationError(motivo_bloqueio, code="em_uso") from erro
    registrar(
        TipoEvento.CADASTRO_EXCLUIDO,
        request=request,
        usuario=por,
        objeto_tipo=rotulo,
        objeto_id=pk,
        valores=valores,
    )


# --- Cursos e coordenação (só Administrador) ---------------------------------------------------


def _so_admin(por):
    def verificar(_instancia):
        if not escopo.pode_cadastrar_cursos(por):
            raise PermissionDenied

    return verificar


def salvar_curso(*, por, dados, curso=None, request=None) -> Curso:
    return _salvar(
        por=por, instancia=curso or Curso(), dados=dados, request=request, verificar=_so_admin(por)
    )


def excluir_curso(*, por, curso, request=None) -> None:
    _excluir(
        por=por,
        instancia=curso,
        request=request,
        verificar=_so_admin(por),
        motivo_bloqueio="O curso tem turmas, disciplinas, diários ou coordenadores vinculados.",
    )


@transaction.atomic
def vincular_coordenador(*, por, curso, usuario, request=None) -> CoordenacaoCurso:
    _so_admin(por)(curso)
    vinculo = CoordenacaoCurso(curso=curso, usuario=usuario)
    vinculo.full_clean()
    vinculo.save()
    registrar(
        TipoEvento.COORDENACAO_ADICIONADA,
        request=request,
        usuario=por,
        objeto=curso,
        coordenador=usuario.email,
    )
    return vinculo


@transaction.atomic
def desvincular_coordenador(*, por, curso, usuario, request=None) -> None:
    _so_admin(por)(curso)
    removidos, _ = CoordenacaoCurso.objects.filter(curso=curso, usuario=usuario).delete()
    if removidos:
        registrar(
            TipoEvento.COORDENACAO_REMOVIDA,
            request=request,
            usuario=por,
            objeto=curso,
            coordenador=usuario.email,
        )


# --- Turmas, disciplinas e diários (Administrador ou Coordenador do curso) ----------------------


def _no_curso(por):
    def verificar(instancia):
        _exigir_curso_gerenciavel(por, instancia.curso if instancia.curso_id else None)

    return verificar


def salvar_turma(*, por, dados, turma=None, request=None) -> Turma:
    return _salvar(
        por=por, instancia=turma or Turma(), dados=dados, request=request, verificar=_no_curso(por)
    )


def excluir_turma(*, por, turma, request=None) -> None:
    _excluir(
        por=por,
        instancia=turma,
        request=request,
        verificar=_no_curso(por),
        motivo_bloqueio="A turma tem diários vinculados. Desvincule os diários antes de excluir.",
    )


def salvar_disciplina(*, por, dados, disciplina=None, request=None) -> Disciplina:
    return _salvar(
        por=por, instancia=disciplina or Disciplina(), dados=dados, request=request, verificar=_no_curso(por)
    )


def excluir_disciplina(*, por, disciplina, request=None) -> None:
    _excluir(
        por=por,
        instancia=disciplina,
        request=request,
        verificar=_no_curso(por),
        motivo_bloqueio="A disciplina tem diários vinculados.",
    )


def salvar_diario(*, por, dados, diario=None, request=None) -> Diario:
    return _salvar(
        por=por, instancia=diario or Diario(), dados=dados, request=request, verificar=_no_curso(por)
    )


def excluir_diario(*, por, diario, request=None) -> None:
    _excluir(
        por=por,
        instancia=diario,
        request=request,
        verificar=_no_curso(por),
        motivo_bloqueio="O diário já tem boletins importados; as versões nunca são apagadas.",
    )
