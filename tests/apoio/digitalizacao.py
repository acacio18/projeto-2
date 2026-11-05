"""Gera versões "digitalizadas" de um boletim em PDF: só imagem, sem camada de texto.

Elas simulam boletins escaneados para os testes de OCR da Etapa 3. A geração é determinística: a
mesma entrada, com as mesmas versões de pypdfium2, Pillow e numpy, produz os mesmos pixels. Por isso
os arquivos não são versionados (passariam de 1 MB); os testes os recriam numa pasta temporária.

Para gerar os arquivos e olhá-los:
    .venv\\Scripts\\python -m tests.apoio.digitalizacao --saida pasta [--variante 300dpi ...]
"""

import argparse
import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

from tests.apoio.boletins import BOLETIM_EXEMPLO

PONTOS_POR_POLEGADA = 72
BRANCO = 255


@dataclass(frozen=True)
class Variante:
    descricao: str
    dpi: int
    rotacao_graus: float = 0.0  # sentido anti-horário
    ruido_desvio: float = 0.0  # desvio-padrão do ruído gaussiano, em níveis de cinza (0 a 255)
    semente: int = 0  # semente do ruído; fixa para a geração ser reprodutível


VARIANTES = {
    "300dpi": Variante("300 dpi, tons de cinza, sem distorção", dpi=300),
    "150dpi": Variante("150 dpi (baixa resolução)", dpi=150),
    "300dpi_inclinado": Variante(
        "300 dpi, inclinado 1,5° e com ruído de scanner",
        dpi=300,
        rotacao_graus=1.5,
        ruido_desvio=8,
        semente=2026,
    ),
    "300dpi_girado90": Variante(
        "300 dpi, página girada 90° (colocada de lado no scanner)", dpi=300, rotacao_graus=90
    ),
}


def rasterizar(origem: Path, variante: Variante) -> list[Image.Image]:
    """Renderiza cada página do PDF como imagem em tons de cinza, aplicando a variante."""
    gerador = np.random.default_rng(variante.semente)
    documento = pdfium.PdfDocument(origem)
    try:
        paginas = []
        for pagina in documento:
            bitmap = pagina.render(scale=variante.dpi / PONTOS_POR_POLEGADA, grayscale=True)
            imagem = bitmap.to_pil().convert("L")  # convert copia os pixels para fora do bitmap
            if variante.rotacao_graus:
                imagem = imagem.rotate(
                    variante.rotacao_graus, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=BRANCO
                )
            if variante.ruido_desvio:
                ruido = gerador.normal(0, variante.ruido_desvio, (imagem.height, imagem.width))
                pixels = np.asarray(imagem, dtype=np.float64) + ruido
                imagem = Image.fromarray(np.clip(pixels.round(), 0, 255).astype(np.uint8))
            paginas.append(imagem)
        return paginas
    finally:
        documento.close()


def impressao_digital(paginas: Sequence[Image.Image]) -> str:
    """SHA-256 dos pixels e tamanhos das páginas, para conferir que a geração é determinística."""
    resumo = hashlib.sha256()
    for imagem in paginas:
        resumo.update(f"{imagem.mode}{imagem.size}".encode())
        resumo.update(imagem.tobytes())
    return resumo.hexdigest()


def gerar(origem: Path, destino: Path, variante: Variante) -> Path:
    """Grava em `destino` um PDF só com as imagens das páginas, na resolução da variante."""
    paginas = rasterizar(origem, variante)
    destino.parent.mkdir(parents=True, exist_ok=True)
    paginas[0].save(destino, "PDF", save_all=True, append_images=paginas[1:], resolution=variante.dpi)
    return destino


def nome_do_arquivo(origem: Path, nome_variante: str) -> str:
    return f"{origem.stem}.{nome_variante}.pdf"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera versões digitalizadas (só imagem) de um boletim em PDF."
    )
    parser.add_argument(
        "--origem", type=Path, default=BOLETIM_EXEMPLO, help="PDF de origem (padrão: o exemplo)"
    )
    parser.add_argument("--saida", type=Path, required=True, help="pasta onde gravar os PDFs gerados")
    parser.add_argument(
        "--variante", choices=sorted(VARIANTES), action="append", help="variante a gerar (padrão: todas)"
    )
    argumentos = parser.parse_args(argv)
    for nome in argumentos.variante or VARIANTES:
        destino = gerar(
            argumentos.origem, argumentos.saida / nome_do_arquivo(argumentos.origem, nome), VARIANTES[nome]
        )
        print(f"{nome}: {destino} ({VARIANTES[nome].descricao})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
