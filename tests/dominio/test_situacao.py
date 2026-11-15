"""Situação projetada (Arts. 88 a 94): estimativa com motivo e artigo, nunca "Reprovado"."""

from decimal import Decimal as D

import pytest

from dominio.regras.parametros import Parametros
from dominio.regras.situacao import (
    Codigo,
    Componente,
    Situacao,
    situacao_do_componente,
    situacao_do_estudante,
)

P = Parametros()


def _sit(**dados) -> Situacao:
    dados.setdefault("notas", [None, None, None, None])
    return situacao_do_componente(Componente(**dados), P)


@pytest.mark.parametrize(
    ("dados", "codigo"),
    [
        ({"cancelado": True}, Codigo.CANCELADO),
        ({"notas": [80, 90, None, None]}, Codigo.EM_CURSO),
        ({"notas": [70, 70, 70, 70]}, Codigo.APROVADO),
        ({"media_disciplina": 70}, Codigo.APROVADO),
        ({"media_disciplina": D("69.99")}, Codigo.AVALIACAO_FINAL),
        ({"media_disciplina": 40}, Codigo.AVALIACAO_FINAL),  # MA = 40 incluída (PRC-02)
        ({"media_disciplina": D("39.99")}, Codigo.AVALIACAO_FINAL_ABAIXO_DE_40),
        ({"media_disciplina": 17}, Codigo.AVALIACAO_FINAL_ABAIXO_DE_40),
        ({"media_disciplina": 16}, Codigo.CONSELHO_4O_BIMESTRE),
        (
            {"media_disciplina": 50, "nota_avaliacao_final": 95, "media_final": 68},
            Codigo.APROVADO_NA_AVALIACAO_FINAL,
        ),
        ({"media_disciplina": 50, "nota_avaliacao_final": 50}, Codigo.APROVADO_NA_AVALIACAO_FINAL),  # MF 50
        ({"media_disciplina": 59, "nota_avaliacao_final": 33, "media_final": 49}, Codigo.CONSELHO_FINAL),
        ({"media_disciplina": 90, "frequencia_global": D("74.9")}, Codigo.RISCO_DE_RETENCAO),
        ({"media_disciplina": 90, "frequencia_global": 75}, Codigo.APROVADO),
    ],
)
def test_situacao_do_componente(dados, codigo):
    assert _sit(**dados).codigo == codigo


def test_motivo_explica_e_cita_artigos():
    s = _sit(media_disciplina=61)
    assert s.nota_minima_af == 34
    assert "precisa de 34 na Avaliação Final" in s.motivo
    assert s.artigos == ("Art. 89", "Art. 91", "Anexo 01")
    assert s.rotulo == "Avaliação Final"
    assert "faltam as notas de 2 etapas" in _sit(notas=[80, 90]).motivo
    assert "falta a nota de 1 etapa" in _sit(notas=[80, 90, 70]).motivo


def test_ma_igual_a_40_so_leva_selo_se_o_parametro_estiver_pendente():
    assert not _sit(media_disciplina=40).pendente
    pendente = Parametros(pendentes=frozenset({"MEDIA_MINIMA_AVALIACAO_FINAL"}))
    assert situacao_do_componente(Componente(notas=[], media_disciplina=40), pendente).pendente
    assert not situacao_do_componente(Componente(notas=[], media_disciplina=41), pendente).pendente


def _comp(codigo: Codigo, optativa=False):
    return (Situacao(codigo, f"motivo {codigo}", ("Art.",)), optativa)


@pytest.mark.parametrize(
    ("codigos", "esperado"),
    [
        ([], Codigo.EM_CURSO),
        ([Codigo.CANCELADO], Codigo.EM_CURSO),
        ([Codigo.APROVADO] * 5, Codigo.APROVADO),
        ([Codigo.APROVADO, Codigo.AVALIACAO_FINAL], Codigo.AVALIACAO_FINAL),
        ([Codigo.AVALIACAO_FINAL, Codigo.AVALIACAO_FINAL_ABAIXO_DE_40], Codigo.AVALIACAO_FINAL_ABAIXO_DE_40),
        ([Codigo.APROVADO, Codigo.EM_CURSO], Codigo.EM_CURSO),
        ([Codigo.AVALIACAO_FINAL_ABAIXO_DE_40] * 3, Codigo.AVALIACAO_FINAL_ABAIXO_DE_40),  # até 3: AF
        ([Codigo.AVALIACAO_FINAL_ABAIXO_DE_40] * 4, Codigo.CONSELHO_4O_BIMESTRE),  # 4 a 6: Conselho
        ([Codigo.AVALIACAO_FINAL_ABAIXO_DE_40] * 6, Codigo.CONSELHO_4O_BIMESTRE),
        ([Codigo.AVALIACAO_FINAL_ABAIXO_DE_40] * 7, Codigo.RISCO_DE_RETENCAO),  # mais de 6: Art. 94 II
        ([Codigo.CONSELHO_4O_BIMESTRE], Codigo.CONSELHO_4O_BIMESTRE),
        ([Codigo.CONSELHO_FINAL] * 3, Codigo.CONSELHO_FINAL),
        ([Codigo.CONSELHO_FINAL] * 4, Codigo.RISCO_DE_RETENCAO),  # Art. 94 III
        ([Codigo.APROVADO, Codigo.RISCO_DE_RETENCAO], Codigo.RISCO_DE_RETENCAO),
    ],
)
def test_situacao_do_estudante_pelos_limites_de_componentes(codigos, esperado):
    assert situacao_do_estudante([_comp(c) for c in codigos], P).codigo == esperado


def test_optativa_nao_conta_para_retencao():
    componentes = [_comp(Codigo.AVALIACAO_FINAL_ABAIXO_DE_40)] * 3 + [
        _comp(Codigo.AVALIACAO_FINAL_ABAIXO_DE_40, optativa=True)
    ]
    assert situacao_do_estudante(componentes, P).codigo == Codigo.AVALIACAO_FINAL_ABAIXO_DE_40
    assert situacao_do_estudante([_comp(Codigo.CONSELHO_FINAL, optativa=True)], P).codigo == Codigo.APROVADO
