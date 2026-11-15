"""Médias do Regimento Didático (Arts. 55, 63, 89 e 91 e Anexo 01).

Os valores são exatos (``Decimal``), sem arredondar: o Regimento não define arredondamento, e o
usuário decidiu (11/11/2026, PRC-01) que o sistema não arredonda por conta própria. Um 69,5 continua
abaixo de 70; quem arredonda, se quiser, é o professor no SUAP, e o valor do boletim é o oficial.
"""

from collections.abc import Sequence
from decimal import ROUND_CEILING, Decimal

from dominio.regras.parametros import Parametros

Numero = int | Decimal


def como_decimal(valor: Numero | str | None) -> Decimal | None:
    if valor is None:
        return None
    if isinstance(valor, float):
        raise TypeError("Use int, str ou Decimal: float perde precisão nas notas.")
    return Decimal(valor)


def media_aritmetica(valores: Sequence[Numero | None]) -> Decimal | None:
    """Art. 55 I: média aritmética das notas presentes (nota ausente não vira zero)."""
    presentes = [como_decimal(v) for v in valores if v is not None]
    if not presentes:
        return None
    return sum(presentes, Decimal(0)) / len(presentes)


def media_anual(notas: Sequence[Numero | None], p: Parametros) -> Decimal | None:
    """Art. 55 II: MA = (MB1 + MB2 + MB3 + MB4) / 4. Só existe com as quatro etapas lançadas."""
    if len(notas) != p.numero_de_bimestres or any(n is None for n in notas):
        return None
    return media_aritmetica(notas)


def precisa_de_recuperacao(nota_da_etapa: Numero | None, p: Parametros) -> bool:
    """Art. 63: recuperação ao fim do bimestre para quem não atingiu a média bimestral (70)."""
    return nota_da_etapa is not None and como_decimal(nota_da_etapa) < p.media_recuperacao_bimestral


def nota_registrada(media_bimestral: Numero, recuperacao: Numero | None) -> Decimal:
    """Art. 63 §1: para registro, prevalece o maior valor entre a média bimestral e a recuperação."""
    media = como_decimal(media_bimestral)
    return media if recuperacao is None else max(media, como_decimal(recuperacao))


def rendimento_satisfatorio(nota_da_etapa: Numero, p: Parametros) -> bool:
    """Art. 64 (interpretação PRC-05, confirmada em 11/11/2026): nota da etapa ≥ 70."""
    return como_decimal(nota_da_etapa) >= p.rendimento_satisfatorio_minimo


def media_final(media_anual_: Numero, avaliacao_final: Numero, p: Parametros) -> Decimal:
    """Art. 91 parágrafo único: MF = (6·MA + 4·AF) / 10."""
    pesos = p.peso_ma_media_final + p.peso_af_media_final
    total = p.peso_ma_media_final * como_decimal(media_anual_) + p.peso_af_media_final * como_decimal(
        avaliacao_final
    )
    return total / pesos


def nota_minima_na_avaliacao_final(media_anual_: Numero, p: Parametros) -> int | None:
    """Art. 89 §1 e Anexo 01: menor nota inteira na AF que leva a MF ≥ 50.

    É a fórmula do Art. 91 resolvida para AF e arredondada para cima, que reproduz o Anexo 01 inteiro
    (MA 69 → 22 … MA 17 → 100). ``None`` quando nem 100 basta (MA abaixo de 17): a aprovação pela AF
    é impossível, e a situação vai ao Conselho de Classe (Art. 89 §2).
    """
    pesos = p.peso_ma_media_final + p.peso_af_media_final
    falta = pesos * p.media_final_aprovacao - p.peso_ma_media_final * como_decimal(media_anual_)
    minima = max(
        int((falta / p.peso_af_media_final).to_integral_value(rounding=ROUND_CEILING)), p.nota_minima
    )
    return minima if minima <= p.nota_maxima else None
