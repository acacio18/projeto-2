"""Estatística descritiva: valores à mão, referência independente (statistics, numpy) e propriedades."""

import statistics
from decimal import Decimal as D

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from dominio.estatistica import descritiva, recuperacao

TOLERANCIA = 1e-9
notas = st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=60)


def test_resumo_calculado_a_mao():
    r = descritiva.resumir([50, 70, 70, 90, None])
    assert (r.n, r.ausentes) == (4, 1)
    assert (r.media, r.mediana, r.modas) == (70, 70, (70,))
    assert r.variancia == 200  # ((−20)² + 0 + 0 + 20²) / 4
    assert r.desvio_padrao == D(200).sqrt()
    assert (r.minimo, r.maximo, r.amplitude) == (50, 90, 40)
    assert (r.q1, r.q3, r.iqr) == (65, 75, 10)  # QUARTIL.INC
    assert r.percentual_satisfatorio == 75
    assert r.percentual_critico == 0
    assert r.coeficiente_de_variacao == D(200).sqrt() / 70 * 100


def test_bordas():
    vazio = descritiva.resumir([None, None])
    assert (vazio.n, vazio.ausentes, vazio.media, vazio.homogeneidade) == (0, 2, None, None)
    um = descritiva.resumir([D("72.5")])
    assert (um.media, um.mediana, um.q1, um.q3, um.desvio_padrao, um.modas) == (D("72.5"),) * 4 + (0, ())
    iguais = descritiva.resumir([80] * 5)
    assert (iguais.variancia, iguais.modas, iguais.homogeneidade) == (0, (80,), "homogênea")
    assert descritiva.resumir([0, 0]).coeficiente_de_variacao is None
    extremos = descritiva.resumir([0, 100])
    assert (extremos.percentual_critico, extremos.percentual_satisfatorio, extremos.modas) == (50, 50, ())
    with pytest.raises(TypeError):
        descritiva.resumir([70.5])


def test_moda_multimodal_e_homogeneidade():
    assert descritiva.modas([D(1), D(1), D(2), D(2), D(3)]) == [1, 2]
    assert descritiva.resumir([70, 72, 74]).homogeneidade == "homogênea"
    assert descritiva.resumir([50, 70, 90]).homogeneidade == "dispersão média"  # CV ≈ 23%
    assert descritiva.resumir([10, 50, 90]).homogeneidade == "heterogênea"


@given(notas)
def test_confere_com_statistics_e_numpy(valores):
    r = descritiva.resumir(valores)
    assert abs(float(r.media) - statistics.fmean(valores)) < TOLERANCIA
    assert abs(float(r.mediana) - statistics.median(valores)) < TOLERANCIA
    assert abs(float(r.variancia) - statistics.pvariance(valores)) < TOLERANCIA
    assert abs(float(r.desvio_padrao) - statistics.pstdev(valores)) < TOLERANCIA
    q1, q3 = np.percentile(valores, [25, 75])  # método linear = QUARTIL.INC
    assert abs(float(r.q1) - q1) < TOLERANCIA
    assert abs(float(r.q3) - q3) < TOLERANCIA
    if len(set(valores)) < len(valores):
        assert [int(m) for m in r.modas] == sorted(statistics.multimode(valores))


@given(notas)
def test_propriedades(valores):
    r = descritiva.resumir(valores)
    assert r.minimo <= r.q1 <= r.mediana <= r.q3 <= r.maximo
    assert r.variancia >= 0
    assert descritiva.resumir(list(reversed(valores))) == r  # a ordem não importa
    faixas = descritiva.distribuicao_por_faixas(valores)
    assert sum(f.quantidade for f in faixas) == len(valores)


def test_faixas_semiabertas():
    faixas = descritiva.distribuicao_por_faixas([0, D("39.99"), 40, 69, 70, 85, 86, 100, None])
    assert [(f.rotulo, f.quantidade) for f in faixas] == [
        ("Crítica", 2),
        ("Mediana", 2),
        ("Boa", 2),
        ("Excelente", 2),
    ]
    assert faixas[0].percentual == 25
    assert all(f.percentual is None for f in descritiva.distribuicao_por_faixas([]))
    outras = descritiva.distribuicao_por_faixas([10, 60], limites=(50,))
    assert [(f.rotulo, f.quantidade) for f in outras] == [("Faixa 1", 1), ("Faixa 2", 1)]


def test_z_score_e_ranking_denso():
    assert descritiva.z_score(90, D(70), D(10)) == 2
    assert descritiva.z_score(70, D(70), D(0)) is None
    ranking = descritiva.posicoes({"a": 90, "b": 80, "c": 90, "d": None, "e": 70})
    assert ranking == {"a": 1, "c": 1, "b": 2, "e": 3}
    assert descritiva.posicoes({}) == {}


def test_recuperacao_entre_bimestres():
    indice = recuperacao.entre_bimestres([[60, 75, None, 80], [50, 55, 72, None], [90, 95, 100, 100]])
    # pares abaixo de 70: (60→75), (50→55), (55→72); (75→None) e (72→None) não contam
    assert (indice.casos, indice.recuperados) == (3, 2)
    assert indice.ganho_medio == D(15 + 5 + 17) / 3
    assert indice.percentual == D(200) / 3
    vazio = recuperacao.entre_bimestres([[80, 90]])
    assert (vazio.casos, vazio.percentual, vazio.ganho_medio) == (0, None, None)


def test_recuperacao_na_avaliacao_final():
    indice = recuperacao.na_avaliacao_final([(50, 95, 68), (59, 33, 49), (80, None, 80), (None, None, None)])
    assert (indice.casos, indice.recuperados, indice.ganho_medio) == (2, 1, D(18 - 10) / 2)
