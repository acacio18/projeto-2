"""Índice de recuperação (ID 24), adaptado ao que o boletim do SUAP traz.

O plano previa comparar a nota antes e depois da recuperação bimestral (Art. 63), mas o boletim só
mostra a nota já registrada (o maior valor entre as duas, Art. 63 §1): a nota da recuperação não vem
separada. Com o que existe, o índice mede duas recuperações que o boletim deixa ver:

- **entre bimestres:** de quem ficou abaixo de 70 numa etapa, quantos chegaram a 70 na etapa seguinte;
- **na Avaliação Final:** de quem fez a AF, quantos chegaram à média final 50 (Art. 91).

É um indicador exploratório; a escolha está em ``docs/planejamento/14-decisoes-pendencias.md``.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal

Numero = int | Decimal


@dataclass(frozen=True)
class IndiceDeRecuperacao:
    casos: int  # quantas oportunidades de recuperação havia
    recuperados: int
    ganho_medio: Decimal | None  # média de (nota depois − nota antes) nesses casos

    @property
    def percentual(self) -> Decimal | None:
        return Decimal(self.recuperados) * 100 / self.casos if self.casos else None


def _indice(pares: Iterable[tuple[Decimal, Decimal]], meta: Numero) -> IndiceDeRecuperacao:
    lista = list(pares)
    if not lista:
        return IndiceDeRecuperacao(0, 0, None)
    recuperados = sum(depois >= meta for _, depois in lista)
    ganho = sum((depois - antes for antes, depois in lista), Decimal(0)) / len(lista)
    return IndiceDeRecuperacao(len(lista), recuperados, ganho)


def entre_bimestres(
    notas_por_aluno: Iterable[Sequence[Numero | None]], meta: Numero = 70
) -> IndiceDeRecuperacao:
    """Pares (etapa k abaixo da meta, etapa k+1 lançada) de cada aluno."""
    pares = []
    for notas in notas_por_aluno:
        for antes, depois in zip(notas, notas[1:], strict=False):
            if antes is not None and depois is not None and Decimal(antes) < meta:
                pares.append((Decimal(antes), Decimal(depois)))
    return _indice(pares, meta)


def na_avaliacao_final(
    alunos: Iterable[tuple[Numero | None, Numero | None, Numero | None]], meta: Numero = 50
) -> IndiceDeRecuperacao:
    """(média anual, nota da AF, média final) de cada aluno; só conta quem fez a AF."""
    pares = [
        (Decimal(ma), Decimal(mf))
        for ma, af, mf in alunos
        if ma is not None and af is not None and mf is not None
    ]
    return _indice(pares, meta)
