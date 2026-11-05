"""Confere o gabarito do boletim de exemplo contra o próprio PDF e contra as contas do boletim.

O gabarito foi transcrito à mão a partir da imagem das páginas. Estes testes garantem que ele bate,
coluna por coluna, com a camada de texto do PDF, e que os números fecham entre si (faltas, frequência,
médias). Assim o gabarito pode servir de referência para o leitor de boletins da Etapa 3.
"""

import hashlib
import re
from decimal import ROUND_HALF_EVEN, Decimal

import pdfplumber
import pytest

from tests.apoio import boletins

ALUNOS = boletins.carregar_gabarito()["alunos"]
LINHA_DE_ALUNO = re.compile(r"^\d+ \d{12} ")


def _id_do_aluno(aluno: dict) -> str:
    return f"aluno{aluno['ordem']:02d}"


def _celula(valor: int | None, sufixo: str = "") -> str:
    return "-" if valor is None else f"{valor}{sufixo}"


def _linha_esperada(aluno: dict) -> str:
    """A linha do aluno como aparece na camada de texto do PDF (colunas separadas por espaço)."""
    partes = [
        str(aluno["ordem"]),
        aluno["matricula"],
        aluno["nome"],
        str(aluno["total_faltas"]),
        _celula(aluno["frequencia_percentual"], "%"),
        aluno["situacao"],
    ]
    for etapa in aluno["etapas"]:
        partes += [_celula(etapa["nota"]), str(etapa["faltas"])]
    partes += [
        _celula(aluno["media_disciplina"]),
        _celula(aluno["avaliacao_final"]["nota"]),
        str(aluno["avaliacao_final"]["faltas"]),
        _celula(aluno["media_final"]),
    ]
    return " ".join(partes)


def _arredondar(valor: Decimal) -> int:
    """Arredonda para inteiro com meio para o par, como o SUAP faz (PRC-01)."""
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


@pytest.fixture(scope="module")
def paginas_em_texto() -> list[str]:
    with pdfplumber.open(boletins.BOLETIM_EXEMPLO) as pdf:
        return [pagina.extract_text() for pagina in pdf.pages]


def test_aponta_para_o_pdf_versionado_com_o_hash_certo(gabarito_exemplo):
    caminho = boletins.caminho_do_pdf(gabarito_exemplo)
    assert caminho == boletins.BOLETIM_EXEMPLO
    assert hashlib.sha256(caminho.read_bytes()).hexdigest() == gabarito_exemplo["sha256"]


def test_numero_de_paginas(gabarito_exemplo, paginas_em_texto):
    assert len(paginas_em_texto) == gabarito_exemplo["paginas"]


def test_cabecalho_confere_com_a_camada_de_texto(gabarito_exemplo, paginas_em_texto):
    g = gabarito_exemplo
    instituicao = g["instituicao"]
    linhas = paginas_em_texto[0].splitlines()
    assert instituicao["nome"] in linhas
    assert f"{instituicao['campus']} - Código INEP: {instituicao['codigo_inep']}" in linhas
    assert instituicao["endereco"] in linhas
    assert instituicao["telefone"] is None
    assert f"CNPJ: {instituicao['cnpj']} - Telefone: None" in linhas
    assert f"Curso: {g['curso']['texto']}" in linhas
    assert f"Diário: {g['diario']['texto']}" in linhas
    periodo, aulas = g["periodo_letivo"]["texto"], g["aulas_ministradas"]["texto"]
    assert f"Ano/Período Letivo: {periodo} Aulas Ministradas: {aulas}" in linhas


def test_campos_do_cabecalho_saem_do_texto(gabarito_exemplo):
    curso, diario = gabarito_exemplo["curso"], gabarito_exemplo["diario"]
    periodo, aulas = gabarito_exemplo["periodo_letivo"], gabarito_exemplo["aulas_ministradas"]
    assert curso["texto"] == f"{curso['codigo']} - {curso['nome']}"
    assert diario["texto"] == (
        f"{diario['codigo']} - {diario['disciplina_codigo']} - {diario['disciplina_nome']} - "
        f"{diario['nivel']} [{diario['carga_horaria_horas']} h/{diario['aulas_previstas']} Aulas]"
    )
    assert periodo["texto"].startswith(f"{periodo['ano']}/{periodo['periodo']} (")
    assert [int(n) for n in re.findall(r"(\d)º", periodo["texto"])] == periodo["etapas"]
    assert aulas["texto"] == f"{aulas['ministradas']} de {aulas['previstas']} Aulas"
    assert aulas["previstas"] == diario["aulas_previstas"]


def test_emissao_e_professor_na_ultima_pagina(gabarito_exemplo, paginas_em_texto):
    emissao = gabarito_exemplo["emissao"]
    ano, mes, dia = emissao["data"].split("-")
    ultima = paginas_em_texto[-1]
    assert f"{emissao['local']}, {dia}/{mes}/{ano}" in ultima.splitlines()
    # No PDF o nome do professor quebra em duas linhas; basta cada palavra estar lá, na ordem.
    palavras = ultima.split()
    posicoes = [palavras.index(parte) for parte in gabarito_exemplo["professor_principal"].split()]
    assert posicoes == sorted(posicoes)
    assert "(Professor Principal)" in ultima


@pytest.mark.parametrize("aluno", ALUNOS, ids=_id_do_aluno)
def test_linha_do_aluno_confere_com_a_camada_de_texto(aluno, paginas_em_texto):
    assert _linha_esperada(aluno) in paginas_em_texto[aluno["pagina"] - 1].splitlines()


def test_nao_ha_aluno_no_pdf_fora_do_gabarito(gabarito_exemplo, paginas_em_texto):
    linhas_de_aluno = [
        linha for texto in paginas_em_texto for linha in texto.splitlines() if LINHA_DE_ALUNO.match(linha)
    ]
    assert len(linhas_de_aluno) == len(gabarito_exemplo["alunos"]) == 32


def test_ordem_matriculas_e_situacoes(gabarito_exemplo):
    alunos = gabarito_exemplo["alunos"]
    assert [a["ordem"] for a in alunos] == list(range(1, len(alunos) + 1))
    matriculas = [a["matricula"] for a in alunos]
    assert len(set(matriculas)) == len(matriculas)
    assert all(re.fullmatch(r"\d{12}", m) for m in matriculas)
    assert {a["situacao"] for a in alunos} == {"Aprovado", "Cancelado"}
    assert [a["ordem"] for a in alunos if a["situacao"] == "Cancelado"] == [24, 30, 31]
    assert all(len(a["etapas"]) == 4 for a in alunos)


@pytest.mark.parametrize("aluno", ALUNOS, ids=_id_do_aluno)
def test_contas_do_aluno_fecham(aluno, gabarito_exemplo):
    """Faltas somam o total; % Freq., MD e MFD batem com o recálculo (meio para o par)."""
    faltas = sum(e["faltas"] for e in aluno["etapas"]) + aluno["avaliacao_final"]["faltas"]
    assert faltas == aluno["total_faltas"]

    if aluno["situacao"] == "Cancelado":
        assert aluno["frequencia_percentual"] is None
        assert aluno["media_disciplina"] is None
        assert aluno["media_final"] is None
        return

    ministradas = gabarito_exemplo["aulas_ministradas"]["ministradas"]
    frequencia = Decimal(ministradas - aluno["total_faltas"]) * 100 / ministradas
    assert aluno["frequencia_percentual"] == _arredondar(frequencia)

    notas = [e["nota"] for e in aluno["etapas"]]
    assert None not in notas
    media = aluno["media_disciplina"]
    assert media == _arredondar(Decimal(sum(notas)) / len(notas))

    nota_final = aluno["avaliacao_final"]["nota"]
    assert (nota_final is not None) == (media < 70)  # nesta amostra, quem ficou abaixo de 70 fez a AF
    esperado = media if nota_final is None else _arredondar(Decimal(6 * media + 4 * nota_final) / 10)
    assert aluno["media_final"] == esperado


def test_ha_empate_em_meio_resolvido_para_o_par(gabarito_exemplo):
    """Evidência da PRC-01: aluna 4 tem notas somando 330 (média 82,5) e MD 82, não 83."""
    beatriz = gabarito_exemplo["alunos"][3]
    assert sum(e["nota"] for e in beatriz["etapas"]) == 330
    assert beatriz["media_disciplina"] == 82
