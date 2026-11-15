"""Situação projetada de um componente e do estudante no ano (Arts. 88 a 94).

É uma **estimativa** (Art. 51, 56 e 92 §2): o resultado oficial é do SUAP e do Conselho de Classe. Por
isso nada aqui diz "Reprovado": quem não alcança a média vai à Avaliação Final, ao Conselho de Classe
ou fica em "risco de retenção", sempre com o motivo e o artigo.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from dominio.regras.medias import (
    Numero,
    como_decimal,
    media_anual,
    media_final,
    nota_minima_na_avaliacao_final,
)
from dominio.regras.parametros import Parametros


class Codigo(StrEnum):
    CANCELADO = "CANCELADO"
    EM_CURSO = "EM_CURSO"
    APROVADO = "APROVADO"
    AVALIACAO_FINAL = "AVALIACAO_FINAL"
    AVALIACAO_FINAL_ABAIXO_DE_40 = "AVALIACAO_FINAL_ABAIXO_DE_40"
    CONSELHO_4O_BIMESTRE = "CONSELHO_4O_BIMESTRE"
    APROVADO_NA_AVALIACAO_FINAL = "APROVADO_NA_AVALIACAO_FINAL"
    CONSELHO_FINAL = "CONSELHO_FINAL"
    RISCO_DE_RETENCAO = "RISCO_DE_RETENCAO"


ROTULOS = {
    Codigo.CANCELADO: "Cancelado",
    Codigo.EM_CURSO: "Em curso",
    Codigo.APROVADO: "Aprovação projetada",
    Codigo.AVALIACAO_FINAL: "Avaliação Final",
    Codigo.AVALIACAO_FINAL_ABAIXO_DE_40: "Avaliação Final (média abaixo de 40)",
    Codigo.CONSELHO_4O_BIMESTRE: "Conselho de Classe do 4º bimestre",
    Codigo.APROVADO_NA_AVALIACAO_FINAL: "Aprovação projetada após a AF",
    Codigo.CONSELHO_FINAL: "Conselho de Classe Final",
    Codigo.RISCO_DE_RETENCAO: "Risco de retenção",
}


@dataclass(frozen=True)
class Situacao:
    codigo: Codigo
    motivo: str
    artigos: tuple[str, ...]
    pendente: bool = False  # usa parâmetro ainda não confirmado institucionalmente
    nota_minima_af: int | None = None

    @property
    def rotulo(self) -> str:
        return ROTULOS[self.codigo]


@dataclass(frozen=True)
class Componente:
    """Os números de um estudante num diário, como vieram do boletim (``None`` = "-")."""

    notas: Sequence[Numero | None]
    media_disciplina: Numero | None = None  # MD do boletim (oficial); sem ela, calcula-se a MA
    nota_avaliacao_final: Numero | None = None
    media_final: Numero | None = None  # MFD do boletim
    cancelado: bool = False
    optativa: bool = False  # Art. 68: língua estrangeira optativa não retém
    frequencia_global: Numero | None = None  # PRC-03: só quando todos os diários da turma estão importados


def _br(valor) -> str:
    """82.750 → "82,75"; 68.00 → "68" (o número como o professor escreve)."""
    return format(valor.normalize(), "f").replace(".", ",")


def _frequencia_baixa(c: Componente, p: Parametros) -> Situacao | None:
    if c.frequencia_global is None or como_decimal(c.frequencia_global) >= p.frequencia_minima_percentual:
        return None
    return Situacao(
        Codigo.RISCO_DE_RETENCAO,
        f"Frequência global de {_br(como_decimal(c.frequencia_global))}% no ano, abaixo de "
        f"{p.frequencia_minima_percentual}%.",
        ("Art. 88", "Art. 94 I"),
    )


def situacao_do_componente(c: Componente, p: Parametros) -> Situacao:
    if c.cancelado:
        return Situacao(Codigo.CANCELADO, "Matrícula cancelada no SUAP: fica fora dos indicadores.", ())
    ma = como_decimal(c.media_disciplina) if c.media_disciplina is not None else media_anual(c.notas, p)
    if ma is None:
        faltam = sum(n is None for n in c.notas) + max(p.numero_de_bimestres - len(c.notas), 0)
        texto = "falta a nota de 1 etapa" if faltam == 1 else f"faltam as notas de {faltam} etapas"
        return Situacao(Codigo.EM_CURSO, f"Ainda sem a média anual: {texto}.", ("Art. 55 II",))
    if baixa := _frequencia_baixa(c, p):
        return baixa
    if ma >= p.media_aprovacao:
        return Situacao(
            Codigo.APROVADO, f"Média anual {_br(ma)}, igual ou acima de {p.media_aprovacao}.", ("Art. 88",)
        )
    if c.nota_avaliacao_final is not None:
        mf = (
            como_decimal(c.media_final)
            if c.media_final is not None
            else media_final(ma, c.nota_avaliacao_final, p)
        )
        if mf >= p.media_final_aprovacao:
            return Situacao(
                Codigo.APROVADO_NA_AVALIACAO_FINAL,
                f"Média final {_br(mf)} após a Avaliação Final, igual ou acima de {p.media_final_aprovacao}.",
                ("Art. 91",),
            )
        return Situacao(
            Codigo.CONSELHO_FINAL,
            f"Média final {_br(mf)}, abaixo de {p.media_final_aprovacao}: vai ao Conselho de Classe Final "
            f"(até {p.limite_componentes_conselho_final} componentes).",
            ("Art. 91", "Art. 92"),
        )
    minima = nota_minima_na_avaliacao_final(ma, p)
    if minima is None:
        return Situacao(
            Codigo.CONSELHO_4O_BIMESTRE,
            f"Média anual {_br(ma)}: nem a nota máxima na Avaliação Final chega à média final "
            f"{p.media_final_aprovacao}. A situação é deliberada pelo Conselho de Classe do 4º bimestre.",
            ("Art. 89 §2", "Anexo 01"),
        )
    if ma >= p.media_minima_avaliacao_final:
        return Situacao(
            Codigo.AVALIACAO_FINAL,
            f"Média anual {_br(ma)}, abaixo de {p.media_aprovacao}: precisa de {minima} na Avaliação Final.",
            ("Art. 89", "Art. 91", "Anexo 01"),
            pendente=ma == p.media_minima_avaliacao_final and p.pendente("MEDIA_MINIMA_AVALIACAO_FINAL"),
            nota_minima_af=minima,
        )
    return Situacao(
        Codigo.AVALIACAO_FINAL_ABAIXO_DE_40,
        f"Média anual {_br(ma)}, abaixo de {p.media_minima_avaliacao_final}: tem Avaliação Final se estiver "
        f"assim em até {p.limite_componentes_af_abaixo_de_40} componentes, e precisa de {minima}.",
        ("Art. 89 §1", "Anexo 01"),
        nota_minima_af=minima,
    )


def situacao_do_estudante(componentes: Iterable[tuple[Situacao, bool]], p: Parametros) -> Situacao:
    """Junta os componentes do ano (situação, optativa) e aplica os limites por número de componentes.

    Arts. 89 §1 e §2, 92, 93 e 94; Art. 68: componente optativo não conta para a retenção.
    """
    lista = [(s, optativa) for s, optativa in componentes if s.codigo != Codigo.CANCELADO]
    contam = [s for s, optativa in lista if not optativa]
    codigos = [s.codigo for s in contam]
    abaixo_de_40 = codigos.count(Codigo.AVALIACAO_FINAL_ABAIXO_DE_40) + codigos.count(
        Codigo.CONSELHO_4O_BIMESTRE
    )
    conselho_final = codigos.count(Codigo.CONSELHO_FINAL)
    if Codigo.RISCO_DE_RETENCAO in codigos:
        return next(s for s in contam if s.codigo == Codigo.RISCO_DE_RETENCAO)
    if abaixo_de_40 > p.limite_componentes_conselho_4o_bimestre:
        return Situacao(
            Codigo.RISCO_DE_RETENCAO,
            f"Média anual abaixo de {p.media_minima_avaliacao_final} em {abaixo_de_40} componentes "
            f"(mais de {p.limite_componentes_conselho_4o_bimestre}).",
            ("Art. 89 §2", "Art. 94 II"),
        )
    if abaixo_de_40 > p.limite_componentes_af_abaixo_de_40 or Codigo.CONSELHO_4O_BIMESTRE in codigos:
        return Situacao(
            Codigo.CONSELHO_4O_BIMESTRE,
            f"Média anual abaixo de {p.media_minima_avaliacao_final} em {abaixo_de_40} componente(s): a "
            "Avaliação Final é deliberada pelo Conselho de Classe do 4º bimestre.",
            ("Art. 89 §2",),
        )
    if conselho_final > p.limite_componentes_conselho_final:
        return Situacao(
            Codigo.RISCO_DE_RETENCAO,
            f"Média final abaixo de {p.media_final_aprovacao} em {conselho_final} componentes "
            f"(mais de {p.limite_componentes_conselho_final}).",
            ("Art. 92", "Art. 94 III"),
        )
    if conselho_final:
        return Situacao(
            Codigo.CONSELHO_FINAL,
            f"Média final abaixo de {p.media_final_aprovacao} em {conselho_final} componente(s): Conselho de "
            f"Classe Final, com possível Progressão Parcial (até {p.limite_componentes_progressao_parcial}).",
            ("Art. 92", "Art. 93"),
        )
    for codigo in (Codigo.EM_CURSO, Codigo.AVALIACAO_FINAL_ABAIXO_DE_40, Codigo.AVALIACAO_FINAL):
        if codigo in codigos:
            pior = next(s for s in contam if s.codigo == codigo)
            return Situacao(codigo, pior.motivo, pior.artigos, pior.pendente)
    if not lista:
        return Situacao(Codigo.EM_CURSO, "Nenhum componente com notas.", ())
    return Situacao(Codigo.APROVADO, "Aprovação projetada em todos os componentes que contam.", ("Art. 88",))
