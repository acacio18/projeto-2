"""Painel inicial de cada perfil (os painéis de turmas e alunos chegam na E6)."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from apps.contas import escopo
from apps.contas.models import Perfil


def inicio(request):
    return redirect("painel")


@login_required
def painel(request):
    contexto = {}
    if escopo.pode_gerenciar_usuarios(request.user):
        contexto["resumo_usuarios"] = escopo.usuarios_visiveis(request.user).aggregate(
            ativos=Count("pk", filter=Q(is_active=True)),
            professores=Count("pk", filter=Q(is_active=True, perfil=Perfil.PROFESSOR)),
            coordenadores=Count("pk", filter=Q(is_active=True, perfil=Perfil.COORDENADOR)),
            convites=Count("pk", filter=Q(is_active=True, password__startswith=UNUSABLE_PASSWORD_PREFIX)),
        )
    return render(request, "paineis/painel.html", contexto)
