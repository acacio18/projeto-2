"""Indicadores de uma versão das notas (IDs 7, 22, 23 e 24), prontos para a tela e para guardar.

Só entram as etapas até o bimestre de corte informado no envio (PRC-17). Cancelados ficam fora das
estatísticas, e quem o professor marcou "fora de rankings e comparações" (Art. 72) fica fora das
estatísticas e do ranking, mas continua com a sua situação e a sua frequência.
"""

from dataclasses import asdict
from decimal import Decimal

from apps.notas import consultas
from dominio.estatistica import descritiva, recuperacao
from dominio.regras import frequencia, medias
from dominio.regras.parametros import Parametros
from dominio.regras.situacao import ROTULOS, Codigo, Componente, situacao_do_componente

VERSAO_DO_CALCULO = "2"
ROTULOS_DO_RESUMO = [
    ("n", "Alunos com nota"),
    ("ausentes", "Sem nota"),
    ("media", "Média"),
    ("mediana", "Mediana"),
    ("modas", "Moda"),
    ("desvio_padrao", "Desvio-padrão"),
    ("minimo", "Mínima"),
    ("maximo", "Máxima"),
    ("q1", "1º quartil"),
    ("q3", "3º quartil"),
    ("coeficiente_de_variacao", "Coeficiente de variação (%)"),
    ("homogeneidade", "Homogeneidade"),
    ("percentual_satisfatorio", "% com 70 ou mais"),
    ("percentual_critico", "% abaixo de 40"),
]


def _texto(valor):
    """Decimal → texto, para o JSON guardar o valor exato."""
    if isinstance(valor, Decimal):
        return format(valor.normalize(), "f")  # 86.000 → "86"; 100 → "100" (sem notação científica)
    if isinstance(valor, list | tuple):
        return [_texto(v) for v in valor]
    return valor


def _resumo(valores, p: Parametros) -> dict:
    resumo = descritiva.resumir(
        valores, satisfatorio=p.rendimento_satisfatorio_minimo, critico=p.media_minima_avaliacao_final
    )
    return {chave: _texto(valor) for chave, valor in asdict(resumo).items()} | {
        "homogeneidade": resumo.homogeneidade
    }


def _alerta_do_conselho(valores, p: Parametros) -> dict:
    """Art. 64 (PRC-05): mais de 30% dos alunos com nota da etapa abaixo de 70 (estritamente maior)."""
    presentes = [v for v in valores if v is not None]
    abaixo = sum(not medias.rendimento_satisfatorio(v, p) for v in presentes)
    percentual = Decimal(abaixo) * 100 / len(presentes) if presentes else None
    return {
        "abaixo": abaixo,
        "percentual": _texto(percentual),
        "dispara": percentual is not None and percentual > p.alerta_conselho_percentual,
    }


def _aulas_ate_o_corte(importacao, corte: int, p: Parametros) -> tuple[int, int]:
    """(aulas dadas até o corte, aulas previstas no ano)."""
    previstas = importacao.diario.aulas_previstas or importacao.aulas_ministradas or 0
    dadas = importacao.aulas_ministradas or 0
    if corte < p.numero_de_bimestres and previstas:
        dadas = min(dadas, previstas * corte // p.numero_de_bimestres)  # boletim completo, corte antes
    return dadas, previstas


def calcular(importacao, p: Parametros) -> dict:
    corte = importacao.bimestre_corte
    completo = corte == p.numero_de_bimestres
    optativa = importacao.diario.disciplina.optativa
    aulas_dadas, aulas_previstas = _aulas_ate_o_corte(importacao, corte, p)
    alunos, referencias, trios_da_af = [], {}, []
    for linha in consultas.linhas_da_versao(importacao):
        por_bimestre = {b.bimestre: b for b in linha.bimestres.all()}
        notas = [
            por_bimestre[k].nota if k in por_bimestre and k <= corte else None
            for k in range(1, p.numero_de_bimestres + 1)
        ]
        componente = Componente(
            notas=notas,
            media_disciplina=linha.media_disciplina if completo else None,
            nota_avaliacao_final=linha.nota_avaliacao_final if completo else None,
            media_final=linha.media_final if completo else None,
            cancelado=linha.cancelado,
            optativa=optativa,
        )
        situacao = situacao_do_componente(componente, p)
        faltas = (
            linha.total_faltas if completo else sum(b.faltas for k, b in por_bimestre.items() if k <= corte)
        )
        if linha.cancelado:
            referencia = None
        elif completo and linha.media_disciplina is not None:
            referencia = componente.media_disciplina
        else:
            referencia = medias.media_aritmetica(notas)
        conta = not linha.cancelado and not linha.matricula.excluir_das_comparacoes
        if conta:
            referencias[linha.ordem] = referencia
            if completo:
                trios_da_af.append((linha.media_disciplina, linha.nota_avaliacao_final, linha.media_final))
        freq = (
            None
            if linha.cancelado
            else frequencia.situacao_de_frequencia(aulas_dadas, aulas_previstas, faltas, p)
        )
        alunos.append(
            {
                "ordem": linha.ordem,
                "nome": linha.nome_no_boletim,
                "cancelado": linha.cancelado,
                "fora_das_comparacoes": linha.matricula.excluir_das_comparacoes,
                "conta": conta,
                "notas": _texto(notas),
                "referencia": _texto(referencia),
                "situacao": {
                    "codigo": situacao.codigo.value,
                    "rotulo": situacao.rotulo,
                    "motivo": situacao.motivo,
                    "artigos": list(situacao.artigos),
                    "pendente": situacao.pendente,
                    "nota_minima_af": situacao.nota_minima_af,
                },
                "frequencia": None
                if freq is None
                else {
                    "presenca": _texto(freq.presenca_ate_agora),
                    "faltas": freq.faltas,
                    "faltas_permitidas": freq.faltas_permitidas,
                    "faltas_restantes": freq.faltas_restantes,
                    "abaixo_do_minimo": freq.abaixo_do_minimo,
                    "em_alerta": freq.em_alerta,
                },
            }
        )

    contam = [a for a in alunos if a["conta"]]
    colunas = []
    for k in range(1, corte + 1):
        valores = [Decimal(a["notas"][k - 1]) if a["notas"][k - 1] is not None else None for a in contam]
        colunas.append(
            {
                "titulo": f"{k}º bim.",
                "resumo": _resumo(valores, p),
                "conselho": _alerta_do_conselho(valores, p),
            }
        )
    if completo:
        valores = [Decimal(a["referencia"]) if a["referencia"] is not None else None for a in contam]
        colunas.append({"titulo": "MD", "resumo": _resumo(valores, p), "conselho": None})

    resumo_da_referencia = descritiva.resumir(referencias.values())
    posicoes = descritiva.posicoes(referencias)
    for aluno in alunos:
        aluno["posicao"] = posicoes.get(aluno["ordem"])
        z = None
        if aluno["conta"] and aluno["referencia"] is not None and resumo_da_referencia.n:
            z = descritiva.z_score(
                Decimal(aluno["referencia"]), resumo_da_referencia.media, resumo_da_referencia.desvio_padrao
            )
        aluno["z"] = _texto(z)

    notas_dos_que_contam = [[Decimal(n) if n is not None else None for n in a["notas"]] for a in contam]
    entre = recuperacao.entre_bimestres(notas_dos_que_contam, meta=p.media_recuperacao_bimestral)
    na_af = recuperacao.na_avaliacao_final(trios_da_af, meta=p.media_final_aprovacao)
    contagem = {}
    for aluno in alunos:
        rotulo = aluno["situacao"]["rotulo"]
        contagem[rotulo] = contagem.get(rotulo, 0) + 1
    return {
        "versao_do_calculo": VERSAO_DO_CALCULO,
        "corte": corte,
        "completo": completo,
        "referencia": "média da disciplina (MD)" if completo else f"média das notas até o {corte}º bimestre",
        "aulas": {"dadas": aulas_dadas, "previstas": aulas_previstas},
        "colunas": colunas,
        "faixas": [
            _texto_faixa(f)
            for f in descritiva.distribuicao_por_faixas(referencias.values(), p.faixas_desempenho)
        ],
        "alunos": alunos,
        "situacoes": [
            {"codigo": c.value, "rotulo": ROTULOS[c], "quantidade": contagem[ROTULOS[c]]}
            for c in Codigo
            if ROTULOS[c] in contagem
        ],
        "recuperacao": {"entre_bimestres": _texto_indice(entre), "na_avaliacao_final": _texto_indice(na_af)},
        "pendentes": sorted(p.pendentes),
    }


def _texto_faixa(faixa) -> dict:
    return {chave: _texto(valor) for chave, valor in asdict(faixa).items()}


def _texto_indice(indice) -> dict:
    return {
        "casos": indice.casos,
        "recuperados": indice.recuperados,
        "percentual": _texto(indice.percentual),
        "ganho_medio": _texto(indice.ganho_medio),
    }
