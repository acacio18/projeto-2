"""Estatística descritiva das notas (ID 7), exata em ``Decimal``.

Convenções (PRC-10, registradas em ``docs/design/formulas-e-indicadores.md``):
- variância e desvio-padrão **populacionais** (a turma inteira é a população, não uma amostra);
- quartis pelo método **inclusivo** (interpolação linear, igual ao QUARTIL.INC do Excel e ao padrão do
  numpy), para o professor conseguir conferir numa planilha;
- nota ausente ("-") fica fora das contas e é contada à parte, nunca vira zero.
"""

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal

Numero = int | Decimal


def _decimais(valores: Iterable[Numero | None]) -> tuple[list[Decimal], int]:
    presentes, ausentes = [], 0
    for valor in valores:
        if valor is None:
            ausentes += 1
        elif isinstance(valor, float):
            raise TypeError("Use int, str ou Decimal: float perde precisão nas notas.")
        else:
            presentes.append(Decimal(valor))
    return presentes, ausentes


def quantil(ordenados: Sequence[Decimal], fracao: Decimal) -> Decimal:
    """Quantil inclusivo (QUARTIL.INC): posição (n − 1)·p com interpolação linear entre vizinhos."""
    posicao = (len(ordenados) - 1) * fracao
    abaixo = int(posicao)
    if abaixo + 1 >= len(ordenados):
        return ordenados[-1]
    return ordenados[abaixo] + (ordenados[abaixo + 1] - ordenados[abaixo]) * (posicao - abaixo)


def modas(valores: Sequence[Decimal]) -> list[Decimal]:
    """Valores mais frequentes, em ordem crescente. Lista vazia quando nenhum se repete ("não há moda")."""
    contagem = Counter(valores)
    maior = max(contagem.values(), default=0)
    if maior < 2:
        return []
    return sorted(v for v, n in contagem.items() if n == maior)


@dataclass(frozen=True)
class Resumo:
    n: int
    ausentes: int
    media: Decimal | None = None
    mediana: Decimal | None = None
    modas: tuple[Decimal, ...] = ()
    variancia: Decimal | None = None  # populacional
    desvio_padrao: Decimal | None = None  # populacional
    minimo: Decimal | None = None
    maximo: Decimal | None = None
    amplitude: Decimal | None = None
    q1: Decimal | None = None
    q3: Decimal | None = None
    iqr: Decimal | None = None
    coeficiente_de_variacao: Decimal | None = None  # % do desvio sobre a média; None se a média é 0
    percentual_satisfatorio: Decimal | None = None  # notas ≥ limiar satisfatório (70)
    percentual_critico: Decimal | None = None  # notas < limiar crítico (40)

    @property
    def homogeneidade(self) -> str | None:
        """Leitura do CV (convenção usual em estatística: até 15% baixa dispersão, até 30% média)."""
        cv = self.coeficiente_de_variacao
        if cv is None:
            return None
        if cv <= 15:
            return "homogênea"
        return "dispersão média" if cv <= 30 else "heterogênea"


def resumir(valores: Iterable[Numero | None], *, satisfatorio: Numero = 70, critico: Numero = 40) -> Resumo:
    presentes, ausentes = _decimais(valores)
    n = len(presentes)
    if n == 0:
        return Resumo(n=0, ausentes=ausentes)
    ordenados = sorted(presentes)
    media = sum(ordenados, Decimal(0)) / n
    variancia = sum(((v - media) ** 2 for v in ordenados), Decimal(0)) / n
    desvio = variancia.sqrt()
    q1, q3 = quantil(ordenados, Decimal("0.25")), quantil(ordenados, Decimal("0.75"))
    return Resumo(
        n=n,
        ausentes=ausentes,
        media=media,
        mediana=quantil(ordenados, Decimal("0.5")),
        modas=tuple(modas(ordenados)),
        variancia=variancia,
        desvio_padrao=desvio,
        minimo=ordenados[0],
        maximo=ordenados[-1],
        amplitude=ordenados[-1] - ordenados[0],
        q1=q1,
        q3=q3,
        iqr=q3 - q1,
        coeficiente_de_variacao=None if media == 0 else desvio / media * 100,
        percentual_satisfatorio=Decimal(sum(v >= satisfatorio for v in ordenados)) * 100 / n,
        percentual_critico=Decimal(sum(v < critico for v in ordenados)) * 100 / n,
    )


def z_score(valor: Numero, media: Decimal, desvio_padrao: Decimal) -> Decimal | None:
    """Quantos desvios-padrão a nota está da média da turma. ``None`` se todos tiraram o mesmo."""
    if desvio_padrao == 0:
        return None
    return (Decimal(valor) - media) / desvio_padrao


@dataclass(frozen=True)
class Faixa:
    rotulo: str
    inicio: int
    fim: int  # exclusivo, exceto na última faixa, que inclui o 100
    quantidade: int
    percentual: Decimal | None


ROTULOS_DAS_FAIXAS = ("Crítica", "Mediana", "Boa", "Excelente")


def distribuicao_por_faixas(
    valores: Iterable[Numero | None], limites: Sequence[int] = (40, 70, 86), maximo: int = 100
) -> list[Faixa]:
    """PRC-06: [0, 40), [40, 70), [70, 86) e [86, 100], intervalos semiabertos (não perdem decimais)."""
    presentes, _ = _decimais(valores)
    bordas = [0, *limites, maximo]
    faixas = []
    for indice, (inicio, fim) in enumerate(zip(bordas, bordas[1:], strict=False)):
        ultima = indice == len(bordas) - 2
        quantidade = sum(inicio <= v < fim or (ultima and v == fim) for v in presentes)
        percentual = Decimal(quantidade) * 100 / len(presentes) if presentes else None
        rotulo = (
            ROTULOS_DAS_FAIXAS[indice]
            if len(bordas) - 1 == len(ROTULOS_DAS_FAIXAS)
            else f"Faixa {indice + 1}"
        )
        faixas.append(Faixa(rotulo, inicio, fim, quantidade, percentual))
    return faixas


def posicoes(valores: dict[object, Numero | None]) -> dict[object, int]:
    """Ranking denso (ID 22): maior nota em 1º, empates na mesma posição, sem pular números.

    Quem não tem nota fica de fora; quem chama exclui antes os marcados "fora de rankings" (Art. 72).
    """
    distintos = sorted({Decimal(v) for v in valores.values() if v is not None}, reverse=True)
    lugar = {valor: indice for indice, valor in enumerate(distintos, start=1)}
    return {chave: lugar[Decimal(v)] for chave, v in valores.items() if v is not None}
