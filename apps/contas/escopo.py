"""Política central de escopo: o que cada usuário pode ver e fazer (ID 2).

TODA consulta de dados de domínio (telas, API, exportações) passa por este módulo. Nenhuma view
filtra por perfil por conta própria. Regras:

- Administrador: vê e gerencia tudo.
- Coordenador: vê e gerencia os cursos que coordena (turmas, disciplinas e diários deles) e vê os
  professores que têm diários nesses cursos. Se também der aulas, vê os próprios diários.
- Professor: vê só os diários dos quais é responsável (e os cursos, turmas e disciplinas deles).

Só o Administrador gerencia usuários e cursos. O vínculo coordenador-curso é mantido pelo
Administrador (PRC-16); o vínculo professor-curso vem dos diários (PRC-12).
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404

from apps.academico.models import Curso, Diario, Disciplina, Turma
from apps.contas.models import Perfil


def esta_ativo(usuario) -> bool:
    return bool(usuario and usuario.is_authenticated and usuario.is_active)


def tem_perfil(usuario, *perfis: str) -> bool:
    return esta_ativo(usuario) and usuario.perfil in perfis


def pode_gerenciar_usuarios(usuario) -> bool:
    return tem_perfil(usuario, Perfil.ADMIN)


def usuarios_visiveis(usuario):
    """Usuários cujo cadastro `usuario` pode ver (o coordenador vê também os professores dos seus cursos)."""
    modelo = get_user_model()
    if pode_gerenciar_usuarios(usuario):
        return modelo.objects.all()
    if tem_perfil(usuario, Perfil.COORDENADOR):
        cursos = cursos_gerenciaveis(usuario)
        return modelo.objects.filter(Q(pk=usuario.pk) | Q(diarios__curso__in=cursos)).distinct()
    if esta_ativo(usuario):
        return modelo.objects.filter(pk=usuario.pk)
    return modelo.objects.none()


# --- Cursos, turmas, disciplinas e diários (E2) ------------------------------------------------


def cursos_gerenciaveis(usuario):
    """Cursos cujos cadastros (turmas, disciplinas, diários) o usuário pode criar e alterar."""
    if pode_gerenciar_usuarios(usuario):
        return Curso.objects.all()
    if tem_perfil(usuario, Perfil.COORDENADOR):
        return Curso.objects.filter(coordenacoes__usuario=usuario)
    return Curso.objects.none()


def pode_gerenciar_curso(usuario, curso) -> bool:
    return cursos_gerenciaveis(usuario).filter(pk=curso.pk).exists()


def pode_cadastrar_cursos(usuario) -> bool:
    """Criar e alterar cursos e vincular coordenadores: só o Administrador."""
    return pode_gerenciar_usuarios(usuario)


def diarios_visiveis(usuario):
    if pode_gerenciar_usuarios(usuario):
        return Diario.objects.all()
    if not esta_ativo(usuario):
        return Diario.objects.none()
    filtro = Q(professor=usuario)
    if tem_perfil(usuario, Perfil.COORDENADOR):
        filtro |= Q(curso__in=cursos_gerenciaveis(usuario))
    return Diario.objects.filter(filtro).distinct()


def diarios_gerenciaveis(usuario):
    """Diários cujo vínculo (turma, professor) o usuário pode alterar: os dos cursos que gerencia."""
    return Diario.objects.filter(curso__in=cursos_gerenciaveis(usuario))


def cursos_visiveis(usuario):
    if pode_gerenciar_usuarios(usuario):
        return Curso.objects.all()
    filtro = Q(pk__in=cursos_gerenciaveis(usuario).values("pk")) | Q(diarios__in=diarios_visiveis(usuario))
    return Curso.objects.filter(filtro).distinct() if esta_ativo(usuario) else Curso.objects.none()


def turmas_visiveis(usuario):
    if pode_gerenciar_usuarios(usuario):
        return Turma.objects.all()
    if not esta_ativo(usuario):
        return Turma.objects.none()
    filtro = Q(curso__in=cursos_gerenciaveis(usuario)) | Q(diarios__in=diarios_visiveis(usuario))
    return Turma.objects.filter(filtro).distinct()


def disciplinas_visiveis(usuario):
    if pode_gerenciar_usuarios(usuario):
        return Disciplina.objects.all()
    if not esta_ativo(usuario):
        return Disciplina.objects.none()
    filtro = Q(curso__in=cursos_gerenciaveis(usuario)) | Q(diarios__in=diarios_visiveis(usuario))
    return Disciplina.objects.filter(filtro).distinct()


def professores_do_curso(curso):
    """Quem tem diário no curso (base da consulta do coordenador, ID 15)."""
    return get_user_model().objects.filter(diarios__curso=curso).distinct().order_by("nome")


def professores_atribuiveis():
    """Quem pode ser professor responsável de um diário: professores e coordenadores ativos."""
    return (
        get_user_model()
        .objects.filter(is_active=True, perfil__in=[Perfil.PROFESSOR, Perfil.COORDENADOR])
        .order_by("nome")
    )


def coordenadores_disponiveis():
    return get_user_model().objects.filter(is_active=True, perfil=Perfil.COORDENADOR).order_by("nome")


def obter_visivel(consulta, pk):
    """Busca dentro do escopo; fora dele, 404 (não revela que o registro existe)."""
    return get_object_or_404(consulta, pk=pk)


def exigir_perfil(usuario, *perfis: str) -> None:
    """Barra (403) quem não tem um dos perfis exigidos para uma área inteira."""
    if not tem_perfil(usuario, *perfis):
        raise PermissionDenied


def obter_usuario_visivel(usuario, pk):
    """Busca um usuário dentro do escopo; fora dele, responde 404 (não revela que o registro existe)."""
    return get_object_or_404(usuarios_visiveis(usuario), pk=pk)
