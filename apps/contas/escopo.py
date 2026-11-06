"""Política central de escopo: o que cada usuário pode ver e fazer (ID 2).

TODA consulta de dados de domínio (telas, API, exportações) passa por este módulo. Nenhuma view
filtra por perfil por conta própria. Regras:

- Administrador: vê e gerencia tudo.
- Coordenador: vê os diários das turmas dos seus cursos (a partir da E2, quando existirem diários).
- Professor: vê só os diários dos quais é responsável (a partir da E2).

Na E1 só existem usuários: apenas o Administrador gerencia usuários, e cada um vê o próprio cadastro.
A consulta dos professores do curso pelo coordenador entra na E2, porque o vínculo professor-curso
vem dos diários (PRC-12 e PRC-16).
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from apps.contas.models import Perfil


def esta_ativo(usuario) -> bool:
    return bool(usuario and usuario.is_authenticated and usuario.is_active)


def tem_perfil(usuario, *perfis: str) -> bool:
    return esta_ativo(usuario) and usuario.perfil in perfis


def pode_gerenciar_usuarios(usuario) -> bool:
    return tem_perfil(usuario, Perfil.ADMIN)


def usuarios_visiveis(usuario):
    """Usuários cujo cadastro `usuario` pode ver."""
    modelo = get_user_model()
    if pode_gerenciar_usuarios(usuario):
        return modelo.objects.all()
    if esta_ativo(usuario):
        return modelo.objects.filter(pk=usuario.pk)
    return modelo.objects.none()


def exigir_perfil(usuario, *perfis: str) -> None:
    """Barra (403) quem não tem um dos perfis exigidos para uma área inteira."""
    if not tem_perfil(usuario, *perfis):
        raise PermissionDenied


def obter_usuario_visivel(usuario, pk):
    """Busca um usuário dentro do escopo; fora dele, responde 404 (não revela que o registro existe)."""
    return get_object_or_404(usuarios_visiveis(usuario), pk=pk)
