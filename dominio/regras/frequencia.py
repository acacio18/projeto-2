"""Frequência (Arts. 77, 88, 89, 94 e 95; PRC-03).

A regra de aprovação usa a frequência **global** do ano: 75% da carga horária total prevista para o ano
letivo (Art. 88), somando todos os componentes (PRC-03). O boletim traz a frequência **por diário**,
que serve de alerta precoce. As faltas são as brutas do boletim: justificativas e abonos (Arts. 78 a
84 e 94 §1) não aparecem nele.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from dominio.regras.parametros import Parametros


def percentual_de_presenca(aulas: int, faltas: int) -> Decimal | None:
    """Presença sobre as aulas consideradas, em % (exato). ``None`` sem aulas."""
    if aulas <= 0:
        return None
    return Decimal(aulas - min(faltas, aulas)) * 100 / aulas


def faltas_permitidas(aulas_previstas: int, p: Parametros) -> int:
    """Art. 77: maior número de faltas que ainda mantém a frequência mínima sobre as aulas previstas."""
    return int(Decimal(aulas_previstas) * p.limite_faltas_percentual / 100)


@dataclass(frozen=True)
class SituacaoDeFrequencia:
    presenca_ate_agora: Decimal | None  # sobre as aulas já dadas
    faltas: int
    faltas_permitidas: int  # no ano, sobre as aulas previstas (Art. 77)
    faltas_restantes: int  # quantas ainda cabem; negativo = limite já passou
    abaixo_do_minimo: bool  # a frequência sobre as aulas previstas já não pode chegar a 75%

    @property
    def em_alerta(self) -> bool:
        """Alerta precoce: as faltas já gastaram mais da metade do que o ano permite."""
        return self.abaixo_do_minimo or self.faltas * 2 > self.faltas_permitidas


def situacao_de_frequencia(
    aulas_dadas: int, aulas_previstas: int, faltas: int, p: Parametros
) -> SituacaoDeFrequencia:
    """Frequência de um componente: presença até agora e quanto ainda falta para o limite do ano."""
    permitidas = faltas_permitidas(aulas_previstas, p)
    return SituacaoDeFrequencia(
        presenca_ate_agora=percentual_de_presenca(aulas_dadas, faltas),
        faltas=faltas,
        faltas_permitidas=permitidas,
        faltas_restantes=permitidas - faltas,
        abaixo_do_minimo=faltas > permitidas,
    )


@dataclass(frozen=True)
class FrequenciaGlobal:
    aulas_previstas: int
    aulas_dadas: int
    faltas: int
    presenca_ate_agora: Decimal | None
    faltas_restantes: int
    abaixo_do_minimo: bool


def frequencia_global(componentes: Iterable[tuple[int, int, int]], p: Parametros) -> FrequenciaGlobal:
    """PRC-03: soma (aulas previstas, aulas dadas, faltas) de todos os componentes do ano da turma.

    Só tem valor normativo quando todos os diários da turma estão importados; quem chama confere isso.
    """
    previstas = dadas = faltas = 0
    for aulas_previstas, aulas_dadas, faltas_do_componente in componentes:
        previstas += aulas_previstas
        dadas += aulas_dadas
        faltas += faltas_do_componente
    permitidas = faltas_permitidas(previstas, p)
    return FrequenciaGlobal(
        aulas_previstas=previstas,
        aulas_dadas=dadas,
        faltas=faltas,
        presenca_ate_agora=percentual_de_presenca(dadas, faltas),
        faltas_restantes=permitidas - faltas,
        abaixo_do_minimo=faltas > permitidas,
    )
