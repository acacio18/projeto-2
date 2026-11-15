"""Limiares usados pelas regras. Os valores vêm de ``notas.ParametroRegra``; aqui ficam os padrões da norma.

As funções de ``dominio.regras`` recebem um ``Parametros`` pronto e não consultam o banco: quem monta o
objeto é ``apps.analytics.parametros.carregar()``. ``pendentes`` guarda as chaves que ainda dependem de
confirmação institucional (``confirmada=False``), para que cada resultado leve o selo.
"""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Parametros:
    nota_minima: int = 0  # Art. 54 §3
    nota_maxima: int = 100  # Art. 54 §3
    numero_de_bimestres: int = 4  # Arts. 11 e 12
    media_recuperacao_bimestral: int = 70  # Art. 63
    media_aprovacao: int = 70  # Art. 88
    frequencia_minima_percentual: int = 75  # Arts. 88, 89 e 94 I
    media_minima_avaliacao_final: int = 40  # Art. 89 caput (MA = 40 incluída: PRC-02)
    limite_componentes_af_abaixo_de_40: int = 3  # Art. 89 §1
    limite_componentes_conselho_4o_bimestre: int = 6  # Art. 89 §2
    peso_ma_media_final: int = 6  # Art. 91
    peso_af_media_final: int = 4  # Art. 91
    media_final_aprovacao: int = 50  # Art. 91
    limite_componentes_conselho_final: int = 3  # Art. 92
    limite_componentes_progressao_parcial: int = 3  # Art. 93
    alerta_conselho_percentual: int = 30  # Art. 64
    rendimento_satisfatorio_minimo: int = 70  # Art. 64 (PRC-05)
    faixas_desempenho: tuple[int, ...] = (40, 70, 86)  # PRC-06 (critério exploratório)
    pendentes: frozenset[str] = field(default_factory=frozenset)

    @property
    def limite_faltas_percentual(self) -> Decimal:
        """Art. 77: faltas além deste percentual da carga horária comprometem a frequência mínima."""
        return Decimal(100 - self.frequencia_minima_percentual)

    def pendente(self, *chaves: str) -> bool:
        """Se algum dos parâmetros usados ainda espera confirmação institucional."""
        return any(chave in self.pendentes for chave in chaves)


# Nome do campo em Parametros → chave em ParametroRegra.
CHAVES = {
    "nota_minima": "NOTA_MINIMA",
    "nota_maxima": "NOTA_MAXIMA",
    "numero_de_bimestres": "NUMERO_DE_BIMESTRES",
    "media_recuperacao_bimestral": "MEDIA_RECUPERACAO_BIMESTRAL",
    "media_aprovacao": "MEDIA_APROVACAO",
    "frequencia_minima_percentual": "FREQUENCIA_MINIMA_PERCENTUAL",
    "media_minima_avaliacao_final": "MEDIA_MINIMA_AVALIACAO_FINAL",
    "limite_componentes_af_abaixo_de_40": "LIMITE_COMPONENTES_AF_ABAIXO_DE_40",
    "limite_componentes_conselho_4o_bimestre": "LIMITE_COMPONENTES_CONSELHO_4O_BIMESTRE",
    "peso_ma_media_final": "PESO_MA_MEDIA_FINAL",
    "peso_af_media_final": "PESO_AF_MEDIA_FINAL",
    "media_final_aprovacao": "MEDIA_FINAL_APROVACAO",
    "limite_componentes_conselho_final": "LIMITE_COMPONENTES_CONSELHO_FINAL",
    "limite_componentes_progressao_parcial": "LIMITE_COMPONENTES_PROGRESSAO_PARCIAL",
    "alerta_conselho_percentual": "ALERTA_CONSELHO_PERCENTUAL",
    "rendimento_satisfatorio_minimo": "RENDIMENTO_SATISFATORIO_MINIMO",
    "faixas_desempenho": "FAIXAS_DESEMPENHO",
}
