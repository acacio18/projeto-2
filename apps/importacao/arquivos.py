"""Recebimento dos arquivos enviados (IDs 3 e 18): conferência básica, ZIP com limites e SHA-256.

Segurança:
- PDF só se o conteúdo começar com a assinatura "%PDF-" (a extensão não basta) e dentro do limite
  de tamanho; a abertura de fato (corrompido, protegido por senha, nº de páginas) é feita na fila.
- ZIP: limite de arquivos e do total descompactado; cada arquivo é lido com teto de bytes, mesmo que
  o ZIP declare um tamanho menor (proteção contra "ZIP-bomba"); ZIP dentro de ZIP e arquivos
  criptografados são ignorados. Nada é extraído para o disco com o nome vindo do ZIP: os PDFs aceitos
  são gravados depois com nome aleatório (Importacao.arquivo).
"""

import hashlib
import io
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

from django.conf import settings

ASSINATURA_PDF = b"%PDF-"
ASSINATURA_ZIP = b"PK\x03\x04"


@dataclass
class ArquivoRecebido:
    nome: str
    conteudo: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.conteudo).hexdigest()

    @property
    def tamanho(self) -> int:
        return len(self.conteudo)


def _limite_pdf() -> int:
    return settings.IMPORTACAO_TAMANHO_MAXIMO_MB * 1024 * 1024


def _limite_lote() -> int:
    return settings.IMPORTACAO_LOTE_MAXIMO_MB * 1024 * 1024


def motivo_para_recusar_pdf(conteudo: bytes) -> str | None:
    if not conteudo:
        return "arquivo vazio"
    if len(conteudo) > _limite_pdf():
        return f"maior que {settings.IMPORTACAO_TAMANHO_MAXIMO_MB} MB"
    if not conteudo[:1024].lstrip().startswith(ASSINATURA_PDF):
        return "não é um PDF (se for foto ou digitalização, salve como PDF antes de enviar)"
    return None


def _ler_com_limite(arquivo_enviado, limite: int) -> bytes:
    partes, total = [], 0
    for parte in arquivo_enviado.chunks():
        total += len(parte)
        if total > limite:
            break
        partes.append(parte)
    return b"".join(partes) if total <= limite else b"\0" * (limite + 1)


def _nome_curto(nome: str) -> str:
    return PurePosixPath(nome.replace("\\", "/")).name or "sem nome"


class Coletor:
    """Junta os PDFs aceitos e os ignorados (com motivo), respeitando os limites do envio."""

    def __init__(self):
        self.aceitos: list[ArquivoRecebido] = []
        self.ignorados: list[dict] = []
        self.total = 0

    def ignorar(self, nome: str, motivo: str) -> None:
        self.ignorados.append({"nome": _nome_curto(nome), "motivo": motivo})

    def cheio(self) -> bool:
        return len(self.aceitos) >= settings.IMPORTACAO_LOTE_MAXIMO_ARQUIVOS

    def aceitar_pdf(self, nome: str, conteudo: bytes) -> None:
        if self.cheio():
            self.ignorar(nome, f"o envio passou de {settings.IMPORTACAO_LOTE_MAXIMO_ARQUIVOS} arquivos")
            return
        if self.total + len(conteudo) > _limite_lote():
            self.ignorar(nome, f"o envio passou de {settings.IMPORTACAO_LOTE_MAXIMO_MB} MB no total")
            return
        if motivo := motivo_para_recusar_pdf(conteudo):
            self.ignorar(nome, motivo)
            return
        if any(a.sha256 == hashlib.sha256(conteudo).hexdigest() for a in self.aceitos):
            self.ignorar(nome, "arquivo repetido neste envio")
            return
        self.total += len(conteudo)
        self.aceitos.append(ArquivoRecebido(_nome_curto(nome), conteudo))

    def abrir_zip(self, nome_zip: str, conteudo: bytes) -> None:
        try:
            pacote = zipfile.ZipFile(io.BytesIO(conteudo))
        except zipfile.BadZipFile:
            self.ignorar(nome_zip, "ZIP corrompido")
            return
        with pacote:
            for info in pacote.infolist():
                nome = info.filename
                curto = _nome_curto(nome)
                if info.is_dir() or curto.startswith(".") or "__MACOSX" in nome:
                    continue
                if info.flag_bits & 0x1:
                    self.ignorar(nome, "arquivo do ZIP protegido por senha")
                elif not curto.lower().endswith(".pdf"):
                    self.ignorar(nome, "dentro do ZIP só são lidos arquivos .pdf")
                elif info.file_size > _limite_pdf():
                    self.ignorar(nome, f"maior que {settings.IMPORTACAO_TAMANHO_MAXIMO_MB} MB")
                elif self.cheio():
                    self.ignorar(
                        nome, f"o envio passou de {settings.IMPORTACAO_LOTE_MAXIMO_ARQUIVOS} arquivos"
                    )
                else:
                    with pacote.open(info) as entrada:
                        dados = entrada.read(_limite_pdf() + 1)  # teto real, não o tamanho declarado
                    self.aceitar_pdf(nome, dados)


def coletar(arquivos_enviados) -> tuple[list[ArquivoRecebido], list[dict]]:
    """Separa os PDFs aceitos (de arquivos soltos ou de ZIPs) e os ignorados, com o motivo."""
    coletor = Coletor()
    for enviado in arquivos_enviados:
        nome = enviado.name or "sem nome"
        if nome.lower().endswith(".zip"):
            conteudo = _ler_com_limite(enviado, _limite_lote())
            if len(conteudo) > _limite_lote():
                coletor.ignorar(nome, f"ZIP maior que {settings.IMPORTACAO_LOTE_MAXIMO_MB} MB")
            elif not conteudo.startswith(ASSINATURA_ZIP):
                coletor.ignorar(nome, "não é um ZIP válido")
            else:
                coletor.abrir_zip(nome, conteudo)
        else:
            coletor.aceitar_pdf(nome, _ler_com_limite(enviado, _limite_pdf()))
    return coletor.aceitos, coletor.ignorados
