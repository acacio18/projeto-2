"""Validação dos dados lidos de um boletim (ID 4, tarefa 5 da E3). Funções puras, sem banco.

Erros impedem a importação (os dados não seriam confiáveis); avisos aparecem na tela de conferência
para o professor decidir. Os valores do boletim são os oficiais: os recálculos (meio para o par,
PRC-01) só conferem e geram aviso, nunca substituem.

Não são verificáveis pelo boletim do SUAP (não traz as avaliações de cada bimestre): a média
bimestral como média das avaliações (RN-02, Art. 55 I) e o mínimo de 2 avaliações (RN-18, Art. 54 §8).
"""

import re
from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_EVEN, Decimal

ERRO, AVISO = "erro", "aviso"


@dataclass
class Problema:
    nivel: str
    mensagem: str
    aluno: str = ""  # "nº 3 – Nome", quando o problema é de um aluno

    def como_dict(self) -> dict:
        return asdict(self)


def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal(1), rounding=ROUND_HALF_EVEN)


def _rotulo(aluno: dict) -> str:
    ordem = aluno.get("ordem")
    return f"nº {ordem} – {aluno.get('nome') or 'sem nome'}" if ordem else aluno.get("nome") or "sem nome"


def _fora_de_0_a_100(valor) -> bool:
    return valor is not None and not isinstance(valor, str) and not (0 <= valor <= 100)


def validar(dados: dict, *, bimestre_corte: int, padrao_matricula: str, ilegiveis=()) -> list[Problema]:
    problemas: list[Problema] = []

    def erro(mensagem, aluno=None):
        problemas.append(Problema(ERRO, mensagem, _rotulo(aluno) if aluno else ""))

    def aviso(mensagem, aluno=None):
        problemas.append(Problema(AVISO, mensagem, _rotulo(aluno) if aluno else ""))

    # Cabeçalho
    faltando = [
        nome
        for nome, valor in [
            ("o curso", dados["curso"]["codigo"]),
            ("o diário", dados["diario"]["codigo"]),
            ("a disciplina", dados["diario"]["disciplina_codigo"]),
            ("o ano/período letivo", dados["periodo_letivo"]["ano"]),
        ]
        if not valor
    ]
    if faltando:
        erro(
            f"Não encontrei no cabeçalho do boletim: {', '.join(faltando)}. "
            "Confira se é o “Boletim de Notas do Diário” do SUAP."
        )
    alunos = dados["alunos"]
    if not alunos:
        erro("O boletim não tem nenhum aluno na tabela.")
        return problemas

    etapas = dados["periodo_letivo"]["etapas"] or [1, 2, 3, 4]
    if bimestre_corte > max(etapas):
        aviso(f"O {bimestre_corte}º bimestre foi informado, mas o boletim cobre só até o {max(etapas)}º.")
    ministradas = dados["aulas_ministradas"]["ministradas"]
    previstas = dados["aulas_ministradas"]["previstas"]
    if ministradas and previstas and ministradas > previstas:
        aviso(f"Aulas ministradas ({ministradas}) acima das previstas ({previstas}).")

    for celula in ilegiveis:
        erro(
            f"Não foi possível ler o campo “{celula['campo']}” do aluno nº {celula['ordem']} "
            f"(texto lido: “{celula['texto']}”). Envie o PDF original exportado do SUAP "
            "ou um escaneamento mais nítido."
        )

    vistos: dict[str, dict] = {}
    ordens = [a["ordem"] for a in alunos if a["ordem"] is not None]
    if ordens != list(range(1, len(alunos) + 1)):
        aviso(
            "A numeração dos alunos (#) não vai de 1 até o total em sequência. "
            "Confira se nenhuma linha faltou."
        )

    for aluno in alunos:
        if not re.fullmatch(padrao_matricula, aluno["matricula"] or ""):
            erro(f"Matrícula “{aluno['matricula']}” fora do formato esperado.", aluno)
        elif aluno["matricula"] in vistos:
            erro(f"Matrícula {aluno['matricula']} aparece mais de uma vez no boletim.", aluno)
        vistos[aluno["matricula"]] = aluno
        _validar_valores(aluno, erro)
        _conferir_contas(aluno, ministradas, aviso)
    depois_do_corte = [
        a for a in alunos if any(e["etapa"] > bimestre_corte and e["nota"] is not None for e in a["etapas"])
    ]
    if depois_do_corte:
        aviso(
            f"{len(depois_do_corte)} aluno(s) têm nota depois do bimestre informado ({bimestre_corte}º). "
            "Essas notas ficam guardadas, mas não entram nas análises até o bimestre informado avançar."
        )
    return problemas


def _validar_valores(aluno, erro) -> None:
    valores = [(f"nota do {e['etapa']}º bimestre", e["nota"]) for e in aluno["etapas"]] + [
        ("média da disciplina", aluno["media_disciplina"]),
        ("nota da avaliação final", aluno["avaliacao_final"]["nota"]),
        ("média final", aluno["media_final"]),
        ("frequência", aluno["frequencia_percentual"]),
    ]
    for campo, valor in valores:
        if _fora_de_0_a_100(valor):
            erro(f"{campo.capitalize()} {valor} fora da faixa de 0 a 100.", aluno)


def _conferir_contas(aluno, ministradas, aviso) -> None:
    cancelado = aluno["situacao"].strip().lower() == "cancelado"
    faltas = sum(e["faltas"] for e in aluno["etapas"]) + aluno["avaliacao_final"]["faltas"]
    if faltas != aluno["total_faltas"]:
        aviso(
            f"As faltas dos bimestres somam {faltas}, mas o total informado é {aluno['total_faltas']}.", aluno
        )
    if cancelado:
        return
    if ministradas and aluno["frequencia_percentual"] is not None:
        calculada = _arredondar(Decimal(ministradas - aluno["total_faltas"]) * 100 / ministradas)
        if calculada != aluno["frequencia_percentual"]:
            aviso(
                f"Frequência informada {aluno['frequencia_percentual']}%, mas {aluno['total_faltas']} faltas "
                f"em {ministradas} aulas dão {calculada}%.",
                aluno,
            )
    notas = [e["nota"] for e in aluno["etapas"]]
    media = aluno["media_disciplina"]
    if media is not None and None not in notas:
        calculada = _arredondar(Decimal(sum(notas)) / len(notas))
        if calculada != media:
            aviso(f"Média da disciplina informada {media}, mas a média das 4 notas dá {calculada}.", aluno)
    final = aluno["avaliacao_final"]["nota"]
    media_final = aluno["media_final"]
    if media is not None and final is not None and isinstance(media_final, int | Decimal):
        calculada = _arredondar((6 * Decimal(media) + 4 * Decimal(final)) / 10)
        if calculada != media_final:
            aviso(
                f"Média final informada {media_final}, mas (6×MD + 4×NAF)/10 dá {calculada} (Art. 91).", aluno
            )


def tem_erro(problemas: list[Problema]) -> bool:
    return any(p.nivel == ERRO for p in problemas)
