"""Extração pelo texto do PDF (o caso normal: o PDF exportado pelo SUAP tem camada de texto)."""

import pdfplumber

from apps.importacao.leitura.modelo import Documento, Pagina


def _limpar(celula: str | None) -> str | None:
    return None if celula is None else " ".join(celula.split())


def extrair(caminho) -> Documento:
    """Uma tabela por página: a maior encontrada pelas linhas desenhadas (a do boletim tem grade)."""
    documento = Documento(metodo="TEXTO")
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            tabela = max(tabelas, key=len) if tabelas else []
            documento.paginas.append(
                Pagina(
                    linhas=[
                        linha.strip() for linha in (pagina.extract_text() or "").splitlines() if linha.strip()
                    ],
                    tabela=[[_limpar(celula) for celula in linha] for linha in tabela],
                )
            )
    return documento
