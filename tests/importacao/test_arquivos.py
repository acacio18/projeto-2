"""Recebimento de arquivos (IDs 3 e 18): PDF de verdade, limites e ZIP seguro."""

import io
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.importacao.arquivos import coletar, motivo_para_recusar_pdf

PDF = b"%PDF-1.4\n" + b"conteudo" * 10
OUTRO_PDF = b"%PDF-1.7\n" + b"outro" * 10


def _enviado(nome, conteudo):
    return SimpleUploadedFile(nome, conteudo)


def _zip(entradas: dict[str, bytes], criptografar: frozenset[str] = frozenset()) -> bytes:
    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w") as pacote:
        for nome, conteudo in entradas.items():
            pacote.writestr(nome, conteudo, compress_type=zipfile.ZIP_DEFLATED)
    dados = bytearray(saida.getvalue())
    # O zipfile zera o bit de criptografia ao gravar; marca no diretório central (é o que a leitura vê).
    posicao = dados.find(b"PK")
    while posicao != -1:
        tamanho_nome = int.from_bytes(dados[posicao + 28 : posicao + 30], "little")
        nome = dados[posicao + 46 : posicao + 46 + tamanho_nome].decode()
        if nome in criptografar:
            dados[posicao + 8] |= 0x1
        posicao = dados.find(b"PK", posicao + 4)
    return bytes(dados)


@pytest.mark.parametrize(
    ("conteudo", "motivo"),
    [(b"", "vazio"), (b"\x89PNG\r\n", "não é um PDF"), (PDF, None), (b"  \n%PDF-1.5 com espaco antes", None)],
)
def test_assinatura_do_pdf(conteudo, motivo):
    resultado = motivo_para_recusar_pdf(conteudo)
    assert (resultado is None) if motivo is None else (motivo in resultado)


def test_pdf_grande_demais(settings):
    settings.IMPORTACAO_TAMANHO_MAXIMO_MB = 1
    grande = PDF + b"x" * (1024 * 1024)
    aceitos, ignorados = coletar([_enviado("grande.pdf", grande)])
    assert aceitos == []
    assert "maior que 1 MB" in ignorados[0]["motivo"]


def test_varios_pdfs_soltos_com_repetido_e_falso():
    aceitos, ignorados = coletar(
        [
            _enviado("a.pdf", PDF),
            _enviado("b.pdf", OUTRO_PDF),
            _enviado("c.pdf", PDF),
            _enviado("foto.pdf", b"\xff\xd8\xff"),
        ]
    )
    assert [a.nome for a in aceitos] == ["a.pdf", "b.pdf"]
    assert aceitos[0].sha256
    assert aceitos[0].tamanho == len(PDF)
    assert {i["nome"]: i["motivo"] for i in ignorados} == {
        "c.pdf": "arquivo repetido neste envio",
        "foto.pdf": "não é um PDF (se for foto ou digitalização, salve como PDF antes de enviar)",
    }


def test_zip_so_le_pdfs_e_ignora_o_resto():
    pacote = _zip(
        {
            "turma A/boletim1.pdf": PDF,
            "turma A/": b"",
            "__MACOSX/._boletim1.pdf": b"lixo",
            ".oculto.pdf": PDF,
            "planilha.xlsx": b"PK...",
            "dentro.zip": _zip({"x.pdf": OUTRO_PDF}),
            "secreto.pdf": OUTRO_PDF,
        },
        criptografar=frozenset({"secreto.pdf"}),
    )
    aceitos, ignorados = coletar([_enviado("lote.zip", pacote)])
    assert [a.nome for a in aceitos] == ["boletim1.pdf"]  # o caminho dentro do ZIP é descartado
    motivos = {i["nome"]: i["motivo"] for i in ignorados}
    assert motivos == {
        "planilha.xlsx": "dentro do ZIP só são lidos arquivos .pdf",
        "dentro.zip": "dentro do ZIP só são lidos arquivos .pdf",
        "secreto.pdf": "arquivo do ZIP protegido por senha",
    }


def test_zip_respeita_os_limites_de_quantidade_e_de_tamanho(settings):
    settings.IMPORTACAO_LOTE_MAXIMO_ARQUIVOS = 2
    pacote = _zip({f"b{n}.pdf": PDF + bytes([n]) for n in range(4)})
    aceitos, ignorados = coletar([_enviado("lote.zip", pacote)])
    assert len(aceitos) == 2
    assert all("passou de 2 arquivos" in i["motivo"] for i in ignorados)

    settings.IMPORTACAO_LOTE_MAXIMO_ARQUIVOS = 50
    settings.IMPORTACAO_TAMANHO_MAXIMO_MB = 1
    bomba = _zip({"bomba.pdf": PDF + b"0" * (3 * 1024 * 1024)})  # comprime para poucos KB
    assert len(bomba) < 100_000
    aceitos, ignorados = coletar([_enviado("lote.zip", bomba)])
    assert aceitos == []
    assert "maior que 1 MB" in ignorados[0]["motivo"]


def test_total_do_envio_tem_limite(settings):
    settings.IMPORTACAO_LOTE_MAXIMO_MB = 1
    meio_mega = PDF + b"y" * (600 * 1024)
    aceitos, ignorados = coletar([_enviado("a.pdf", meio_mega), _enviado("b.pdf", meio_mega + b"z")])
    assert len(aceitos) == 1
    assert "passou de 1 MB no total" in ignorados[0]["motivo"]


def test_zip_corrompido_falso_ou_grande(settings):
    aceitos, ignorados = coletar(
        [_enviado("quebrado.zip", b"PK\x03\x04" + b"lixo"), _enviado("falso.zip", b"nao e zip")]
    )
    assert aceitos == []
    assert [i["motivo"] for i in ignorados] == ["ZIP corrompido", "não é um ZIP válido"]
    settings.IMPORTACAO_LOTE_MAXIMO_MB = 1
    _, ignorados = coletar([_enviado("enorme.zip", b"PK\x03\x04" + b"0" * (2 * 1024 * 1024))])
    assert "ZIP maior que 1 MB" in ignorados[0]["motivo"]


def test_quantidade_maxima_tambem_vale_para_pdfs_soltos(settings):
    settings.IMPORTACAO_LOTE_MAXIMO_ARQUIVOS = 1
    aceitos, ignorados = coletar([_enviado("a.pdf", PDF), _enviado("b.pdf", OUTRO_PDF)])
    assert len(aceitos) == 1
    assert "passou de 1 arquivos" in ignorados[0]["motivo"]


def test_pdf_grande_declarado_no_zip_e_ignorado_sem_ler(settings):
    settings.IMPORTACAO_TAMANHO_MAXIMO_MB = 1
    pacote = _zip({"grande.pdf": PDF + b"1" * (2 * 1024 * 1024)})
    _, ignorados = coletar([_enviado("lote.zip", pacote)])
    assert ignorados == [{"nome": "grande.pdf", "motivo": "maior que 1 MB"}]
