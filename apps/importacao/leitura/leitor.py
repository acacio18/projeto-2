"""Ponto de entrada da leitura: verifica o PDF, tenta o texto e, se não houver, usa OCR."""

from dataclasses import dataclass, field

import pypdfium2 as pdfium
from django.conf import settings

from apps.importacao.leitura import ocr, perfil_suap, texto
from apps.importacao.leitura.modelo import ErroDeLeitura

VERSAO_LEITOR = "1.0"


@dataclass
class Leitura:
    dados: dict
    metodo: str  # "TEXTO" ou "OCR"
    paginas: int
    perfil: str = perfil_suap.NOME
    confianca: float | None = None
    ilegiveis: list[dict] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    versao: str = VERSAO_LEITOR


def verificar_pdf(caminho) -> int:
    """Abre o PDF e devolve o número de páginas; recusa arquivo corrompido, protegido ou grande demais."""
    try:
        pdf = pdfium.PdfDocument(caminho)
    except pdfium.PdfiumError as erro:
        if "password" in str(erro).lower():
            raise ErroDeLeitura(
                "O PDF está protegido por senha. Exporte o boletim de novo pelo SUAP, sem senha."
            ) from erro
        raise ErroDeLeitura("O arquivo não pôde ser aberto como PDF (pode estar corrompido).") from erro
    try:
        paginas = len(pdf)
    finally:
        pdf.close()
    if paginas == 0:
        raise ErroDeLeitura("O PDF não tem nenhuma página.")
    if paginas > settings.IMPORTACAO_MAXIMO_PAGINAS:
        raise ErroDeLeitura(
            f"O PDF tem {paginas} páginas; o limite é {settings.IMPORTACAO_MAXIMO_PAGINAS}. "
            "Envie um boletim por arquivo (ou use o envio em lote)."
        )
    return paginas


def ler_boletim(caminho, *, usar_ocr: bool = True) -> Leitura:
    paginas = verificar_pdf(caminho)
    documento = texto.extrair(caminho)
    dados, ilegiveis, avisos = perfil_suap.interpretar(documento)
    if not dados["alunos"] and usar_ocr:
        documento = ocr.extrair(caminho, perfil_suap.coluna_e_texto, perfil_suap.coluna_chave)
        dados, ilegiveis, avisos = perfil_suap.interpretar(documento)
    if not dados["alunos"]:
        raise ErroDeLeitura(
            "Não encontrei a tabela de alunos do “Boletim de Notas do Diário” neste PDF. "
            "Confira se é o relatório certo do SUAP."
        )
    return Leitura(
        dados=dados,
        metodo=documento.metodo,
        paginas=paginas,
        confianca=documento.confianca,
        ilegiveis=ilegiveis,
        avisos=avisos,
    )
