"""Prepara os indicadores guardados para a tela (números no formato brasileiro, etiquetas e ícones)."""

from decimal import Decimal

from django.template.defaultfilters import floatformat

from apps.analytics.indicadores import ROTULOS_DO_RESUMO

# Código da situação projetada → (estilo da etiqueta, ícone). A cor nunca vem sozinha: há texto e ícone.
ESTILOS = {
    "APROVADO": ("sucesso", "circle-check"),
    "APROVADO_NA_AVALIACAO_FINAL": ("sucesso", "circle-check"),
    "AVALIACAO_FINAL": ("aviso", "triangle-alert"),
    "AVALIACAO_FINAL_ABAIXO_DE_40": ("aviso", "triangle-alert"),
    "CONSELHO_4O_BIMESTRE": ("erro", "circle-alert"),
    "CONSELHO_FINAL": ("erro", "circle-alert"),
    "RISCO_DE_RETENCAO": ("erro", "circle-alert"),
    "EM_CURSO": ("neutra", "history"),
    "CANCELADO": ("neutra", "circle-x"),
}

MODAS_LISTADAS = 3  # acima disso, a lista de modas não ajuda a ler a turma


def numero(valor, casas: str = "-2") -> str:
    """ "82.75" → "82,75"; "70" → "70"; vazio → "–"."""
    if valor is None:
        return "–"
    return floatformat(Decimal(valor), casas)


def _celula(chave: str, resumo: dict) -> str:
    valor = resumo.get(chave)
    if chave == "modas":
        if not valor:
            return "não há"
        if len(valor) > MODAS_LISTADAS:
            return f"{len(valor)} notas empatadas"
        return ", ".join(numero(v) for v in valor)
    if chave == "coeficiente_de_variacao":
        return numero(valor, "1")
    if chave == "homogeneidade":
        return valor or "–"
    if chave.startswith("percentual") and valor is not None:
        return f"{numero(valor, '-1')}%"
    return numero(valor)


def tabela_de_estatisticas(dados: dict) -> list[dict]:
    """Linhas (indicador) × colunas (etapas e MD), já formatadas."""
    return [
        {"rotulo": rotulo, "valores": [_celula(chave, coluna["resumo"]) for coluna in dados["colunas"]]}
        for chave, rotulo in ROTULOS_DO_RESUMO
    ]


def para_a_tela(dados: dict) -> dict:
    alunos = []
    for aluno in dados["alunos"]:
        estilo, icone = ESTILOS[aluno["situacao"]["codigo"]]
        alunos.append(
            aluno | {"estilo": estilo, "icone": icone, "referencia_formatada": numero(aluno["referencia"])}
        )
    alertas = [
        {
            "etapa": coluna["titulo"],
            "abaixo": coluna["conselho"]["abaixo"],
            "percentual": numero(coluna["conselho"]["percentual"], "-1"),
        }
        for coluna in dados["colunas"]
        if coluna["conselho"] and coluna["conselho"]["dispara"]
    ]
    return dados | {
        "estatisticas": tabela_de_estatisticas(dados),
        "alunos": alunos,
        "alertas_do_conselho": alertas,
        "faixas": [f | {"percentual_formatado": numero(f["percentual"], "-1")} for f in dados["faixas"]],
        "situacoes": [
            s | dict(zip(("estilo", "icone"), ESTILOS[s["codigo"]], strict=True)) for s in dados["situacoes"]
        ],
        "tem_fora_das_comparacoes": any(a["fora_das_comparacoes"] for a in alunos),
        "recuperacao_formatada": {
            nome: indice
            | {
                "percentual_formatado": numero(indice["percentual"], "-1"),
                "ganho": numero(indice["ganho_medio"], "-1"),
            }
            for nome, indice in dados["recuperacao"].items()
        },
    }
