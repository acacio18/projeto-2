"""Indicadores de uma versão (IDs 7, 22, 23 e 24) com o boletim de exemplo do SUAP."""

import datetime
import statistics
from decimal import Decimal

import pytest

from apps.academico.models import MatriculaDiario
from apps.analytics import parametros, servicos
from apps.analytics.models import SnapshotIndicadores
from apps.importacao import servicos as versoes
from apps.notas.models import ParametroRegra
from tests.apoio.boletins_simulados import ate_o_bimestre
from tests.apoio.fabricas import ProfessorFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def professor():
    return ProfessorFactory()


def _versao(professor, dados, corte=4, sha="a" * 64):
    return versoes.registrar_versao(por=professor, dados=dados, bimestre_corte=corte, sha256=sha)


def _ativos(gabarito):
    return [a for a in gabarito["alunos"] if a["situacao"] != "Cancelado"]


def test_estatisticas_por_etapa_e_da_md(professor, gabarito_exemplo):
    dados = servicos.indicadores_da_versao(_versao(professor, gabarito_exemplo))
    assert [c["titulo"] for c in dados["colunas"]] == ["1º bim.", "2º bim.", "3º bim.", "4º bim.", "MD"]
    md = dados["colunas"][-1]["resumo"]
    esperadas = [a["media_disciplina"] for a in _ativos(gabarito_exemplo)]
    assert md["n"] == len(esperadas) == 29
    assert abs(float(Decimal(md["media"])) - statistics.fmean(esperadas)) < 1e-9
    assert abs(float(Decimal(md["desvio_padrao"])) - statistics.pstdev(esperadas)) < 1e-9
    primeira = [a["etapas"][0]["nota"] for a in _ativos(gabarito_exemplo)]
    assert dados["colunas"][0]["resumo"]["mediana"] == str(Decimal(statistics.median(primeira)))
    abaixo = sum(n < 70 for n in primeira)
    assert dados["colunas"][0]["conselho"]["abaixo"] == abaixo
    assert dados["colunas"][0]["conselho"]["dispara"] is (abaixo * 100 / len(primeira) > 30)
    assert sum(f["quantidade"] for f in dados["faixas"]) == 29
    assert dados["pendentes"] == []


def test_situacao_projetada_ranking_e_frequencia(professor, gabarito_exemplo):
    dados = servicos.indicadores_da_versao(_versao(professor, gabarito_exemplo))
    contagem = {s["rotulo"]: s["quantidade"] for s in dados["situacoes"]}
    assert contagem == {"Cancelado": 3, "Aprovação projetada": 26, "Aprovação projetada após a AF": 3}
    por_ordem = {a["ordem"]: a for a in dados["alunos"]}
    assert por_ordem[8]["situacao"]["codigo"] == "APROVADO_NA_AVALIACAO_FINAL"  # Daniel: MD 50, MFD 68
    assert por_ordem[24]["posicao"] is None  # cancelado fica fora do ranking
    melhor = max(_ativos(gabarito_exemplo), key=lambda a: a["media_disciplina"])
    assert por_ordem[melhor["ordem"]]["posicao"] == 1
    aline = por_ordem[1]["frequencia"]  # 4 faltas em 80 aulas
    assert (Decimal(aline["presenca"]), aline["faltas_permitidas"], aline["faltas_restantes"]) == (95, 20, 16)
    assert por_ordem[24]["frequencia"] is None
    na_af = dados["recuperacao"]["na_avaliacao_final"]
    assert (na_af["casos"], na_af["recuperados"]) == (3, 3)


def test_corte_antes_do_fim_ignora_as_etapas_seguintes(professor, gabarito_exemplo):
    dados = servicos.indicadores_da_versao(_versao(professor, gabarito_exemplo, corte=2))
    assert [c["titulo"] for c in dados["colunas"]] == ["1º bim.", "2º bim."]
    assert {s["rotulo"] for s in dados["situacoes"]} == {"Em curso", "Cancelado"}
    assert dados["aulas"] == {"dadas": 40, "previstas": 80}  # metade das aulas até o 2º bimestre
    aline = next(a for a in dados["alunos"] if a["ordem"] == 1)
    assert aline["notas"][2:] == [None, None]
    assert Decimal(aline["referencia"]) == Decimal(50 + 85) / 2
    assert aline["frequencia"]["faltas"] == 4  # só as faltas do 1º e do 2º bimestres
    assert dados["recuperacao"]["na_avaliacao_final"]["casos"] == 0


def test_boletim_ate_o_primeiro_bimestre(professor, gabarito_exemplo):
    dados = servicos.indicadores_da_versao(_versao(professor, ate_o_bimestre(gabarito_exemplo, 1), corte=1))
    assert [c["titulo"] for c in dados["colunas"]] == ["1º bim."]
    assert dados["recuperacao"]["entre_bimestres"] == {
        "casos": 0,
        "recuperados": 0,
        "percentual": None,
        "ganho_medio": None,
    }


def test_snapshot_e_reaproveitado_e_refeito_quando_algo_muda(professor, gabarito_exemplo):
    importacao = _versao(professor, gabarito_exemplo)
    primeiro = servicos.indicadores_da_versao(importacao)
    assert servicos.indicadores_da_versao(importacao) == primeiro
    assert SnapshotIndicadores.objects.count() == 1
    aline = MatriculaDiario.objects.get(diario=importacao.diario, estudante__matricula="201927621032")
    aline.excluir_das_comparacoes = True  # Art. 72
    aline.save()
    depois = servicos.indicadores_da_versao(importacao)
    assert SnapshotIndicadores.objects.count() == 2
    assert depois["colunas"][-1]["resumo"]["n"] == 28
    linha = next(a for a in depois["alunos"] if a["ordem"] == 1)
    assert (linha["posicao"], linha["z"], linha["fora_das_comparacoes"]) == (None, None, True)
    assert linha["situacao"]["codigo"] == "APROVADO"  # continua com a situação própria


def test_parametros_do_banco_e_selo_de_pendente(professor, gabarito_exemplo):
    regras = parametros.carregar()
    assert (regras.media_aprovacao, regras.faixas_desempenho, regras.pendentes) == (
        70,
        (40, 70, 86),
        frozenset(),
    )
    ParametroRegra.objects.create(
        chave="FAIXAS_DESEMPENHO",
        valor="50;75;90",
        tipo="TEXTO",
        descricao="Teste",
        fundamento="Teste",
        confirmada=False,
        vigente_desde=datetime.date(2020, 1, 1),
    )
    novas = parametros.carregar(em=datetime.date(2023, 12, 31))
    assert (novas.faixas_desempenho, novas.pendentes) == ((50, 75, 90), frozenset({"FAIXAS_DESEMPENHO"}))
    assert parametros.assinatura(novas) != parametros.assinatura(regras)
    dados = servicos.indicadores_da_versao(_versao(professor, gabarito_exemplo))
    assert [f["inicio"] for f in dados["faixas"]] == [0, 50, 75, 90]
    assert dados["pendentes"] == ["FAIXAS_DESEMPENHO"]
    ParametroRegra.objects.all().delete()
    assert parametros.carregar().media_aprovacao == 70  # sem linhas no banco, vale a norma
