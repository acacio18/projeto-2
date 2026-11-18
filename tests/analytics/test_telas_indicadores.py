"""Indicadores na tela do diário: estatísticas, faixas, situação projetada, alertas e formato brasileiro."""

import pytest
from django.urls import reverse

from apps.analytics import apresentacao
from apps.analytics.models import SnapshotIndicadores
from apps.importacao import servicos as versoes
from tests.apoio import boletins_simulados as simulados
from tests.apoio.fabricas import ProfessorFactory

pytestmark = pytest.mark.django_db


def _abrir(client, dados, corte=4):
    professor = ProfessorFactory()
    importacao = versoes.registrar_versao(por=professor, dados=dados, bimestre_corte=corte, sha256="c" * 64)
    client.force_login(professor)
    url = reverse("diarios:detalhe", args=[importacao.diario_id]) + "?aba=indicadores"
    return client.get(url).content.decode(), importacao


def test_abas_separam_as_notas_da_analise(client, gabarito_exemplo):
    professor = ProfessorFactory()
    importacao = versoes.registrar_versao(
        por=professor, dados=gabarito_exemplo, bimestre_corte=4, sha256="d" * 64
    )
    client.force_login(professor)
    url = reverse("diarios:detalhe", args=[importacao.diario_id])
    notas = client.get(url).content.decode()
    assert '<nav class="abas" id="abas" aria-label="Conteúdo do diário">' in notas
    assert f'href="?importacao={importacao.pk}#abas" aria-current="page"' in notas
    assert f'href="?importacao={importacao.pk}&amp;aba=indicadores#abas"' in notas
    assert "Notas aguardando confirmação" in notas
    assert "Estatísticas por etapa" not in notas
    assert not SnapshotIndicadores.objects.exists()  # a análise só é calculada quando a aba é aberta
    analise = client.get(url + "?aba=indicadores").content.decode()
    assert f'href="?importacao={importacao.pk}&amp;aba=indicadores#abas" aria-current="page"' in analise
    assert "Estatísticas por etapa" in analise
    assert "Notas aguardando confirmação" not in analise
    assert "tabela--notas" not in analise  # a tabela de notas fica na outra aba
    assert (
        "Estatísticas por etapa" not in client.get(url + "?aba=outra").content.decode()
    )  # aba inválida: notas


def test_diario_mostra_os_indicadores_da_versao(client, gabarito_exemplo):
    html, importacao = _abrir(client, gabarito_exemplo)
    for texto in [
        "Indicadores das notas aguardando confirmação",
        "Situação projetada",
        "Aprovação projetada após a AF",
        "Faixas de desempenho",
        "Estatísticas por etapa",
        "Desvio-padrão populacional",
        "Situação de cada estudante",
        "Média final 68 após a Avaliação Final",  # Daniel
        "(Art. 91)",
        "16 faltas até o limite",  # Aline: 4 de 20 permitidas
        "chegaram à média final 50",
    ]:
        assert texto in html, texto
    assert SnapshotIndicadores.objects.filter(importacao=importacao).count() == 1


def test_alerta_do_conselho_e_situacoes_de_risco(client):
    html, _ = _abrir(client, simulados.dados_completos(simulados.DISCIPLINAS[3]))  # Matemática III
    assert "Alerta para o Conselho de Classe:" in html
    assert "1º bim.: 14 alunos (48,3%)" in html
    assert "notas empatadas" in html
    assert "(Regimento, Art. 64)" in html
    assert "Conselho de Classe Final" in html
    assert "etiqueta--erro" in html


def test_diario_em_andamento(client, gabarito_exemplo):
    html, _ = _abrir(client, simulados.ate_o_bimestre(gabarito_exemplo, 2), corte=2)
    assert "Em curso" in html
    assert "Média até agora" in html
    assert "notas até o 2º bimestre" in html
    assert "Ninguém fez a Avaliação Final nesta versão." in html


def test_diario_sem_notas_nao_mostra_indicadores(client):
    from tests.apoio.fabricas import DiarioFactory

    professor = ProfessorFactory()
    diario = DiarioFactory(professor=professor)
    client.force_login(professor)
    assert "Indicadores" not in client.get(reverse("diarios:detalhe", args=[diario.pk])).content.decode()


def test_numeros_no_formato_brasileiro():
    assert apresentacao.numero("82.75") == "82,75"
    assert apresentacao.numero("70") == "70"
    assert apresentacao.numero(None) == "–"
    resumo = {"modas": [], "coeficiente_de_variacao": None, "percentual_critico": None}
    assert apresentacao._celula("modas", resumo) == "não há"
    assert apresentacao._celula("coeficiente_de_variacao", resumo) == "–"
    assert apresentacao._celula("homogeneidade", {"homogeneidade": None}) == "–"
    assert apresentacao._celula("homogeneidade", {"homogeneidade": "homogênea"}) == "homogênea"
    assert apresentacao._celula("percentual_critico", resumo) == "–"
    assert str(SnapshotIndicadores(importacao_id=7, assinatura="x")) == "Indicadores da importação 7 (x)"
