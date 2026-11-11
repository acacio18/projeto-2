"""Validação dos dados lidos: erros bloqueiam; avisos vão para a conferência do professor."""

import copy

import pytest

from apps.importacao.validacao import AVISO, ERRO, tem_erro, validar
from tests.apoio.boletins import carregar_gabarito

PADRAO = r"^\d{12}$"


@pytest.fixture
def dados():
    return carregar_gabarito()


def _mensagens(problemas, nivel):
    return [p.mensagem for p in problemas if p.nivel == nivel]


def test_boletim_correto_nao_tem_problemas(dados):
    assert validar(dados, bimestre_corte=4, padrao_matricula=PADRAO) == []


def test_cabecalho_incompleto_e_sem_alunos_sao_erros(dados):
    dados["diario"]["codigo"] = None
    dados["periodo_letivo"]["ano"] = None
    dados["alunos"] = []
    problemas = validar(dados, bimestre_corte=4, padrao_matricula=PADRAO)
    assert tem_erro(problemas)
    erros = _mensagens(problemas, ERRO)
    assert "o diário" in erros[0]
    assert "o ano/período letivo" in erros[0]
    assert "nenhum aluno" in erros[1]


def test_matricula_invalida_ou_repetida_e_nota_fora_da_faixa(dados):
    dados["alunos"][0]["matricula"] = "123"
    dados["alunos"][2]["matricula"] = dados["alunos"][1]["matricula"]
    dados["alunos"][3]["etapas"][0]["nota"] = 101
    dados["alunos"][4]["frequencia_percentual"] = -1
    erros = _mensagens(validar(dados, bimestre_corte=4, padrao_matricula=PADRAO), ERRO)
    assert any("Matrícula “123”" in e for e in erros)
    assert any("aparece mais de uma vez" in e for e in erros)
    assert any("Nota do 1º bimestre 101 fora da faixa" in e for e in erros)
    assert any("Frequência -1 fora da faixa" in e for e in erros)


def test_celulas_ilegiveis_sao_erro(dados):
    problemas = validar(
        dados,
        bimestre_corte=4,
        padrao_matricula=PADRAO,
        ilegiveis=[{"ordem": 7, "campo": "faltas", "texto": "?"}],
    )
    assert any("aluno nº 7" in p.mensagem and p.nivel == ERRO for p in problemas)


def test_contas_que_nao_fecham_viram_avisos(dados):
    aline = dados["alunos"][0]
    aline["total_faltas"] = 9  # faltas e frequência
    aline["media_disciplina"] = 80  # MD
    diego = dados["alunos"][8]
    diego["media_final"] = 70  # MFD (Art. 91)
    avisos = _mensagens(validar(dados, bimestre_corte=4, padrao_matricula=PADRAO), AVISO)
    assert any("somam 4, mas o total informado é 9" in a for a in avisos)
    assert any("Frequência informada 95%" in a for a in avisos)
    assert any("a média das 4 notas dá 75" in a for a in avisos)
    assert any("Média final informada 70" in a and "(Art. 91)" in a for a in avisos)


def test_avisos_de_corte_numeracao_e_aulas(dados):
    dados["aulas_ministradas"]["ministradas"] = 90
    dados["alunos"][1]["ordem"] = 99
    dados["periodo_letivo"]["etapas"] = [1, 2]
    problemas = validar(copy.deepcopy(dados), bimestre_corte=3, padrao_matricula=PADRAO)
    avisos = _mensagens(problemas, AVISO)
    assert not tem_erro(problemas)
    assert any("o boletim cobre só até o 2º" in a for a in avisos)
    assert any("Aulas ministradas (90) acima das previstas (80)" in a for a in avisos)
    assert any("numeração dos alunos" in a for a in avisos)
    notas_depois = [a for a in avisos if "depois do bimestre informado (3º)" in a]
    assert len(notas_depois) == 1  # um aviso só, com a contagem


def test_cancelados_nao_entram_na_conferencia_de_medias(dados):
    cancelado = dados["alunos"][29]  # Vanessa: cancelada com notas parciais
    assert cancelado["situacao"] == "Cancelado"
    assert validar(dados, bimestre_corte=4, padrao_matricula=PADRAO) == []


def test_problema_como_dicionario(dados):
    dados["alunos"][0]["total_faltas"] = 0
    problema = validar(dados, bimestre_corte=4, padrao_matricula=PADRAO)[0]
    assert problema.como_dict() == {
        "nivel": AVISO,
        "mensagem": "As faltas dos bimestres somam 4, mas o total informado é 0.",
        "aluno": "nº 1 – Aline Santana Ramos de Jesus",
    }


def test_aluno_ativo_sem_frequencia_nem_media_nao_gera_aviso_de_conta(dados):
    aluno = dados["alunos"][0]
    aluno["frequencia_percentual"] = None
    aluno["media_disciplina"] = None
    aluno["media_final"] = None
    assert validar(dados, bimestre_corte=4, padrao_matricula=PADRAO) == []
