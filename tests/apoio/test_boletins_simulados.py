"""Os boletins simulados são lidos pelo sistema exatamente como foram gerados, sem erro nem aviso."""

import pytest

from apps.importacao.leitura import ler_boletim
from apps.importacao.validacao import validar
from tests.apoio import boletins_simulados as simulados

CAMPOS = [
    "ordem", "matricula", "nome", "total_faltas", "frequencia_percentual", "situacao",
    "etapas", "media_disciplina", "avaliacao_final", "media_final",
]  # fmt: skip
SERIES = {nome: (dados, corte) for nome, dados, corte in simulados.series()}


def test_series_completas():
    assert len(SERIES) == 4 * 7
    assert all(nome.endswith(".pdf") for nome in SERIES)


@pytest.mark.parametrize(
    "nome",
    [
        "70764_analise-e-projeto-de-sistema_ate-o-2o-bimestre_notas-faltando.pdf",
        "70765_programacao-para-web_ate-o-1o-bimestre.pdf",
        "70768_banco-de-dados_ate-o-3o-bimestre.pdf",
        "70771_matematica-iii_completo.pdf",
    ],
)
def test_leitor_extrai_os_valores_gerados(tmp_path, nome):
    dados, corte = SERIES[nome]
    leitura = ler_boletim(simulados.gerar_pdf(dados, tmp_path / nome), usar_ocr=False)
    lidos = leitura.dados
    assert leitura.metodo == "TEXTO"
    assert lidos["diario"]["codigo"] == dados["diario"]["codigo"]
    assert lidos["diario"]["disciplina_nome"] == dados["diario"]["disciplina_nome"]
    assert lidos["aulas_ministradas"]["ministradas"] == dados["aulas_ministradas"]["ministradas"]
    assert [{c: a[c] for c in CAMPOS} for a in lidos["alunos"]] == [
        {c: a[c] for c in CAMPOS} for a in dados["alunos"]
    ]
    assert validar(lidos, bimestre_corte=corte, padrao_matricula=r"^\d{12}$") == []


def test_cada_bimestre_acumula_os_anteriores():
    completo = simulados.dados_completos(simulados.DISCIPLINAS[3])
    ate_2 = simulados.ate_o_bimestre(completo, 2)
    ate_3 = simulados.ate_o_bimestre(completo, 3)
    for aluno2, aluno3 in zip(ate_2["alunos"], ate_3["alunos"], strict=True):
        assert aluno2["etapas"][:2] == aluno3["etapas"][:2]
        assert aluno3["etapas"][3]["nota"] is None
    assert ate_2["aulas_ministradas"]["ministradas"] == 80  # metade das 160 aulas


def test_notas_faltando_ficam_ausentes_e_nao_zero():
    completo = simulados.dados_completos(simulados.ORIGINAL)
    dados = simulados.ate_o_bimestre(completo, 3, simulados.NOTAS_FALTANDO)
    aluno = next(a for a in dados["alunos"] if a["ordem"] == 12)
    assert [e["nota"] for e in aluno["etapas"]][:3] == [
        None,
        completo["alunos"][11]["etapas"][1]["nota"],
        None,
    ]
