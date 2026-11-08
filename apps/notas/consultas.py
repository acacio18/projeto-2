"""Consultas às versões das notas de um diário (sempre a partir de um diário já dentro do escopo)."""

from django.db.models import Prefetch

from apps.importacao.models import Importacao, StatusImportacao
from apps.notas.models import RegistroBimestral, ResultadoAluno


def versoes(diario):
    """Versões confirmadas, da mais nova para a mais antiga."""
    return diario.importacoes.filter(status=StatusImportacao.CONFIRMADA).order_by("-numero_versao")


def versao_vigente(diario) -> Importacao | None:
    return diario.importacoes.filter(vigente=True).first()


def pendentes(diario):
    """Importações registradas que ainda esperam a confirmação do professor."""
    return diario.importacoes.filter(status=StatusImportacao.AGUARDANDO_CONFIRMACAO).order_by("-criada_em")


def linhas_da_versao(importacao):
    """Alunos da versão, na ordem do boletim, com as notas por bimestre já carregadas."""
    return (
        ResultadoAluno.objects.filter(importacao=importacao)
        .select_related("matricula__estudante")
        .prefetch_related(Prefetch("bimestres", queryset=RegistroBimestral.objects.order_by("bimestre")))
        .order_by("ordem")
    )
