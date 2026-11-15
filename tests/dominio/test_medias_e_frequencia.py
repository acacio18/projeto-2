"""Regras de médias e frequência do Regimento (funções puras, sem banco)."""

from decimal import Decimal as D

import pytest

from dominio.regras import frequencia, medias
from dominio.regras.parametros import Parametros

P = Parametros()

# Anexo 01 do Regimento 2024 (pág. 29), transcrito do PDF: média anual → nota mínima na AF.
ANEXO_01 = {
    69: 22, 68: 23, 67: 25, 66: 26, 65: 28, 64: 29, 63: 31, 62: 32, 61: 34, 60: 35, 59: 37, 58: 38,
    57: 40, 56: 41, 55: 43, 54: 44, 53: 46, 52: 47, 51: 49, 50: 50, 49: 52, 48: 53, 47: 55, 46: 56,
    45: 58, 44: 59, 43: 61, 42: 62, 41: 64, 40: 65, 39: 67, 38: 68, 37: 70, 36: 71, 35: 73, 34: 74,
    33: 76, 32: 77, 31: 79, 30: 80, 29: 82, 28: 83, 27: 85, 26: 86, 25: 88, 24: 89, 23: 91, 22: 92,
    21: 94, 20: 95, 19: 97, 18: 98, 17: 100,
}  # fmt: skip


def test_anexo_tem_os_53_pontos():
    assert sorted(ANEXO_01) == list(range(17, 70))


@pytest.mark.parametrize(("media_anual", "minima"), ANEXO_01.items())
def test_nota_minima_na_af_reproduz_o_anexo_01(media_anual, minima):
    assert medias.nota_minima_na_avaliacao_final(media_anual, P) == minima
    assert medias.media_final(media_anual, minima, P) >= 50  # a mínima basta…
    assert medias.media_final(media_anual, minima - 1, P) < 50  # …e uma a menos não


def test_nota_minima_fora_da_tabela():
    assert medias.nota_minima_na_avaliacao_final(16, P) is None  # nem 100 basta: Conselho (Art. 89 §2)
    assert medias.nota_minima_na_avaliacao_final(D("16.7"), P) == 100
    assert medias.nota_minima_na_avaliacao_final(D("69.5"), P) == 21
    assert medias.nota_minima_na_avaliacao_final(90, P) == 0  # nunca negativa


def test_media_anual_so_com_as_quatro_etapas():
    assert medias.media_anual([50, 85, 75, 90], P) == 75
    assert medias.media_anual([71, 75, 85, 100], P) == D("82.75")  # exata, sem arredondar
    assert medias.media_anual([50, None, 75, 90], P) is None
    assert medias.media_anual([50, 85, 75], P) is None


def test_media_aritmetica_ignora_ausente_e_recusa_float():
    assert medias.media_aritmetica([10, None, 20]) == 15
    assert medias.media_aritmetica([None, None]) is None
    assert medias.como_decimal(None) is None
    with pytest.raises(TypeError):
        medias.media_aritmetica([69.5])


@pytest.mark.parametrize(
    ("nota", "esperado"), [(D("69.99"), True), (70, False), (D("70.01"), False), (None, False)]
)
def test_recuperacao_bimestral_abaixo_de_70(nota, esperado):
    assert medias.precisa_de_recuperacao(nota, P) is esperado


def test_nota_registrada_e_a_maior():
    assert medias.nota_registrada(60, 75) == 75
    assert medias.nota_registrada(60, 50) == 60
    assert medias.nota_registrada(60, None) == 60


def test_rendimento_satisfatorio_e_media_final():
    assert medias.rendimento_satisfatorio(70, P)
    assert not medias.rendimento_satisfatorio(D("69.9"), P)
    assert medias.media_final(50, 95, P) == 68  # Daniel, no boletim de exemplo
    assert medias.media_final(D("61.25"), 35, P) == D("50.75")


def test_sem_arredondamento_69_e_meio_nao_aprova():
    assert medias.media_anual([69, 70, 70, 69], P) == D("69.5")
    assert not medias.rendimento_satisfatorio(D("69.5"), P)


def test_frequencia_e_limite_de_faltas():
    assert frequencia.percentual_de_presenca(80, 4) == 95
    assert frequencia.percentual_de_presenca(0, 0) is None
    assert frequencia.percentual_de_presenca(10, 15) == 0  # faltas acima das aulas não dão negativo
    assert frequencia.faltas_permitidas(80, P) == 20
    assert frequencia.faltas_permitidas(67, P) == 16  # 25% de 67 = 16,75: a 17ª falta já passa
    s = frequencia.situacao_de_frequencia(40, 80, 12, P)
    assert (s.presenca_ate_agora, s.faltas_restantes, s.abaixo_do_minimo, s.em_alerta) == (70, 8, False, True)
    s = frequencia.situacao_de_frequencia(80, 80, 20, P)
    assert (s.presenca_ate_agora, s.faltas_restantes, s.abaixo_do_minimo) == (
        75,
        0,
        False,
    )  # 75% exato aprova
    assert frequencia.situacao_de_frequencia(80, 80, 21, P).abaixo_do_minimo
    assert not frequencia.situacao_de_frequencia(20, 80, 2, P).em_alerta


def test_frequencia_global_soma_os_componentes():
    g = frequencia.frequencia_global([(80, 40, 10), (160, 80, 30)], P)
    assert (g.aulas_previstas, g.aulas_dadas, g.faltas, g.faltas_restantes) == (240, 120, 40, 20)
    assert g.presenca_ate_agora == D(80) * 100 / 120
    assert not g.abaixo_do_minimo
    assert frequencia.frequencia_global([], P).presenca_ate_agora is None


def test_parametros_pendentes():
    p = Parametros(pendentes=frozenset({"FAIXAS_DESEMPENHO"}))
    assert p.pendente("FAIXAS_DESEMPENHO", "MEDIA_APROVACAO")
    assert not p.pendente("MEDIA_APROVACAO")
    assert p.limite_faltas_percentual == 25
