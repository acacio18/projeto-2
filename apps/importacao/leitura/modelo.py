"""Estruturas comuns à extração por texto e por OCR."""

from dataclasses import dataclass, field

ILEGIVEL = "?"  # célula com tinta que o OCR não conseguiu ler (nunca vira "ausente" em silêncio)


class ErroDeLeitura(Exception):
    """Problema que impede a leitura. A mensagem é mostrada ao professor, então é escrita para ele."""


@dataclass
class Pagina:
    linhas: list[str]  # texto da página em ordem (cabeçalho, rodapé e, no PDF com texto, a tabela também)
    tabela: list[list[str | None]]  # linhas × colunas; None = célula mesclada com a anterior
    confianca: float | None = None  # média da confiança do OCR (0 a 100); None no PDF com texto


@dataclass
class Documento:
    paginas: list[Pagina] = field(default_factory=list)
    metodo: str = "TEXTO"  # "TEXTO" ou "OCR"

    @property
    def confianca(self) -> float | None:
        valores = [p.confianca for p in self.paginas if p.confianca is not None]
        return round(sum(valores) / len(valores), 1) if valores else None
