"""Extração por OCR, para boletins escaneados (sem camada de texto) — ID 5.

Passos, por página:
1. renderiza a página (pypdfium2, padrão 300 dpi) em tons de cinza;
2. corrige a orientação (página de lado ou de ponta-cabeça) pela OSD do Tesseract;
3. corrige a inclinação (até ±3°) pelo perfil de projeção das linhas;
4. binariza (limiar de Otsu) e localiza a grade da tabela (linhas horizontais e verticais longas);
5. apaga a grade (as bordas grudavam nos dígitos e derrubavam o OCR) e lê cada coluna separadamente:
   nas colunas de números só valem algarismos, "-" e "%", o que impede ler "0" como "O";
6. célula com uma pequena marca horizontal e sem texto lido é o traço "-" (ausente); célula com tinta
   e sem leitura vira ILEGIVEL e bloqueia a importação (nunca vira "ausente" em silêncio).

Medido no boletim de exemplo: 99,3% a 99,8% dos campos corretos a 300 e 150 dpi, inclinado e girado
(relatório em docs/evidencias/E3-acuracia-leitor.md).
"""

from collections.abc import Callable

import numpy as np
import pypdfium2 as pdfium
import pytesseract
from django.conf import settings
from PIL import Image

from apps.importacao.leitura.modelo import ILEGIVEL, Documento, ErroDeLeitura, Pagina

BRANCO = 255
MARGEM = 5  # pixels ignorados junto às linhas da grade
NUMEROS = "0123456789-%,"


def _tesseract():
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    return pytesseract


def limiar_otsu(cinza: np.ndarray) -> int:
    """Limiar que melhor separa tinta e fundo (método de Otsu)."""
    histograma = np.bincount(cinza.ravel(), minlength=256).astype(float)
    total, soma_total = cinza.size, float(np.dot(np.arange(256), histograma))
    peso_fundo = soma_fundo = 0.0
    melhor, limiar = -1.0, 128
    for valor in range(256):
        peso_fundo += histograma[valor]
        if peso_fundo == 0:
            continue
        peso_tinta = total - peso_fundo
        if peso_tinta == 0:
            break
        soma_fundo += valor * histograma[valor]
        media_fundo = soma_fundo / peso_fundo
        media_tinta = (soma_total - soma_fundo) / peso_tinta
        separacao = peso_fundo * peso_tinta * (media_fundo - media_tinta) ** 2
        if separacao > melhor:
            melhor, limiar = separacao, valor
    return limiar


def binarizar(imagem: Image.Image) -> np.ndarray:
    """True onde há tinta."""
    cinza = np.asarray(imagem.convert("L"))
    return cinza < limiar_otsu(cinza)


def angulo_de_inclinacao(tinta: np.ndarray, limite: float = 3.0, passo: float = 0.1) -> float:
    """Ângulo (graus) que deixa as linhas de texto e da grade mais "retas" (maior variância por linha)."""
    reduzida = Image.fromarray((tinta * 255).astype(np.uint8)).resize(
        (max(1, tinta.shape[1] // 4), max(1, tinta.shape[0] // 4))
    )
    melhor, angulo = -1.0, 0.0
    for candidato in np.arange(-limite, limite + passo / 2, passo):
        girada = np.asarray(reduzida.rotate(candidato, resample=Image.Resampling.BILINEAR, fillcolor=0)) > 127
        variancia = float(girada.sum(axis=1).astype(float).var())
        if variancia > melhor:
            melhor, angulo = variancia, float(candidato)
    return round(angulo, 1)


def corrigir_orientacao(imagem: Image.Image) -> tuple[Image.Image, int]:
    """Gira páginas de lado ou de ponta-cabeça (OSD do Tesseract). Sem texto suficiente, não gira."""
    try:
        osd = _tesseract().image_to_osd(imagem, output_type=pytesseract.Output.DICT, config="--psm 0")
    except pytesseract.TesseractError:
        return imagem, 0
    rotacao = int(osd.get("rotate", 0)) % 360
    if rotacao:
        imagem = imagem.rotate(-rotacao, expand=True, fillcolor=BRANCO)
    return imagem, rotacao


def _corridas(linha: np.ndarray) -> list[tuple[int, int]]:
    """Intervalos [início, fim) de tinta contínua numa linha de pixels."""
    bordas = np.diff(np.concatenate(([0], linha.astype(np.int8), [0])))
    return list(zip(np.where(bordas == 1)[0], np.where(bordas == -1)[0], strict=True))


def _agrupar(posicoes: list[int], distancia: int = 4) -> list[int]:
    grupos: list[list[int]] = []
    for posicao in posicoes:
        if grupos and posicao - grupos[-1][-1] <= distancia:
            grupos[-1].append(posicao)
        else:
            grupos.append([posicao])
    return [int(round(sum(g) / len(g))) for g in grupos]


def _verticais_na_faixa(tinta: np.ndarray, y0: int, y1: int) -> list[int]:
    """Linhas verticais que atravessam a faixa entre duas linhas horizontais."""
    faixa = tinta[y0 + 3 : y1 - 2]
    if faixa.shape[0] < 3:
        return []
    return _agrupar(np.where(faixa.mean(axis=0) > 0.9)[0].tolist())


def localizar_grade(tinta: np.ndarray, minimo_colunas: int = 3) -> tuple[list[int], list[int]]:
    """Linhas horizontais e verticais da tabela de alunos. Listas vazias se não houver tabela.

    A tabela é a maior sequência de faixas (entre linhas horizontais) cortadas por várias linhas
    verticais; isso descarta a caixa do título, que só tem as duas bordas laterais.
    """
    altura, largura = tinta.shape
    minimo = int(largura * 0.3)
    ys = _agrupar([y for y in range(altura) if any(f - i >= minimo for i, f in _corridas(tinta[y]))])
    faixas = [_verticais_na_faixa(tinta, y0, y1) for y0, y1 in zip(ys, ys[1:], strict=False)]
    melhor: tuple[int, int] = (0, 0)
    inicio = None
    for indice, verticais in enumerate([*faixas, []]):
        if len(verticais) >= minimo_colunas:
            inicio = indice if inicio is None else inicio
        elif inicio is not None:
            if indice - inicio > melhor[1] - melhor[0]:
                melhor = (inicio, indice)
            inicio = None
    if melhor[1] - melhor[0] < 1:
        return [], []
    ys_tabela = ys[melhor[0] : melhor[1] + 1]
    regiao = tinta[ys_tabela[0] : ys_tabela[-1] + 1]
    xs = _agrupar(np.where(regiao.sum(axis=0) > (ys_tabela[-1] - ys_tabela[0]) * 0.6)[0].tolist())
    return ys_tabela, xs


def apagar_grade(tinta: np.ndarray, ys: list[int], xs: list[int], espessura: int = 4) -> np.ndarray:
    limpa = tinta.copy()
    for y in ys:
        limpa[max(0, y - espessura) : y + espessura + 1, :] = False
    for x in xs:
        limpa[:, max(0, x - espessura) : x + espessura + 1] = False
    return limpa


def _imagem(tinta: np.ndarray, escala: int = 1, borda: int = 20) -> Image.Image:
    imagem = Image.fromarray(np.where(tinta, 0, BRANCO).astype(np.uint8))
    if escala > 1:
        imagem = imagem.resize((imagem.width * escala, imagem.height * escala), Image.Resampling.LANCZOS)
    return Image.fromarray(np.pad(np.asarray(imagem), borda, constant_values=BRANCO))


def ler_texto(imagem: Image.Image) -> list[str]:
    """Texto corrido de uma região em tons de cinza (cabeçalho ou rodapé): o Tesseract binariza melhor."""
    if imagem.height < 10 or not binarizar(imagem).any():
        return []
    texto = _tesseract().image_to_string(imagem, lang="por", config="--psm 6")
    return [linha.strip() for linha in texto.splitlines() if linha.strip()]


def classificar_celula_vazia(celula: np.ndarray) -> str:
    """Célula sem leitura: "" (em branco), "-" (traço) ou ILEGIVEL (tem tinta que não foi lida)."""
    linhas, colunas = np.nonzero(celula)
    if len(linhas) == 0:
        return ""
    altura = linhas.max() - linhas.min() + 1
    largura = colunas.max() - colunas.min() + 1
    if altura <= max(4, celula.shape[0] * 0.2) and largura >= altura * 1.5:
        return "-"
    return ILEGIVEL


def _ler_coluna(tinta, ys, x0, x1, so_numeros: bool, escala: int) -> list[tuple[float, str, float]]:
    """(posição vertical do centro, palavra, confiança) de cada palavra lida numa coluna."""
    faixa = tinta[ys[0] : ys[-1], x0 + MARGEM : x1 - MARGEM + 1]
    config = "--psm 6" + (f" -c tessedit_char_whitelist={NUMEROS}" if so_numeros else "")
    dados = _tesseract().image_to_data(
        _imagem(faixa, escala), lang="por", config=config, output_type=pytesseract.Output.DICT
    )
    palavras = []
    for i, palavra in enumerate(dados["text"]):
        if palavra.strip():
            centro = (dados["top"][i] + dados["height"][i] / 2 - 20) / escala + ys[0]
            palavras.append((centro, palavra.strip(), float(dados["conf"][i])))
    return palavras


def _linha_da_posicao(ys, centro) -> int | None:
    for r, (y0, y1) in enumerate(zip(ys, ys[1:], strict=False)):
        if y0 <= centro < y1:
            return r
    return None


def ler_tabela(
    tinta: np.ndarray,
    ys: list[int],
    xs: list[int],
    coluna_e_texto: Callable[[int, int], bool],
    coluna_chave: int | None = None,
) -> tuple[list[list[str]], float | None]:
    """Lê a tabela coluna por coluna e encaixa cada palavra na sua linha pela posição vertical.

    As linhas de cabeçalho da tabela não são lidas: com o filtro de números, os rótulos viram lixo e
    atrapalham a segmentação do Tesseract. Os dados começam na primeira linha em que a coluna-chave
    (a matrícula) tem um número longo.
    """
    escala = 2 if tinta.shape[1] < 2500 else 1  # abaixo de ~300 dpi, ampliar ajuda o Tesseract
    n_colunas = len(xs) - 1
    n_linhas = len(ys) - 1
    tabela = [[""] * n_colunas for _ in range(n_linhas)]
    primeira = 0
    if coluna_chave is not None and coluna_chave < n_colunas:
        chave = _ler_coluna(tinta, ys, xs[coluna_chave], xs[coluna_chave + 1], True, escala)
        linhas = [_linha_da_posicao(ys, c) for c, palavra, _ in chave if len(palavra) >= 8]
        primeira = min((r for r in linhas if r is not None), default=0)
    ys_dados = ys[primeira:]
    confiancas: list[float] = []
    for c, (x0, x1) in enumerate(zip(xs, xs[1:], strict=False)):
        for centro, palavra, confianca in _ler_coluna(
            tinta, ys_dados, x0, x1, not coluna_e_texto(c, n_colunas), escala
        ):
            r = _linha_da_posicao(ys, centro)
            if r is not None and r >= primeira:
                tabela[r][c] = f"{tabela[r][c]} {palavra}".strip()
                if confianca >= 0:
                    confiancas.append(confianca)
    for r in range(primeira, n_linhas):
        y0, y1 = ys[r], ys[r + 1]
        for c, (x0, x1) in enumerate(zip(xs, xs[1:], strict=False)):
            if not tabela[r][c]:
                celula = tinta[y0 + MARGEM : y1 - MARGEM + 1, x0 + MARGEM : x1 - MARGEM + 1]
                tabela[r][c] = classificar_celula_vazia(celula)
    confianca = round(sum(confiancas) / len(confiancas), 1) if confiancas else None
    return tabela, confianca


def ler_pagina(
    imagem: Image.Image, coluna_e_texto: Callable[[int, int], bool], coluna_chave: Callable[[int], int | None]
) -> Pagina:
    imagem, _ = corrigir_orientacao(imagem.convert("L"))
    tinta = binarizar(imagem)
    angulo = angulo_de_inclinacao(tinta)
    if abs(angulo) >= 0.1:
        imagem = imagem.rotate(angulo, resample=Image.Resampling.BICUBIC, fillcolor=BRANCO)
        tinta = binarizar(imagem)
    ys, xs = localizar_grade(tinta)
    if not ys:
        return Pagina(linhas=ler_texto(imagem), tabela=[])
    limpa = apagar_grade(tinta, ys, xs)
    tabela, confianca = ler_tabela(limpa, ys, xs, coluna_e_texto, coluna_chave(len(xs) - 1))
    acima = imagem.crop((0, 0, imagem.width, max(1, ys[0] - 2)))
    abaixo = imagem.crop((0, min(imagem.height - 1, ys[-1] + 3), imagem.width, imagem.height))
    linhas = ler_texto(acima) + ler_texto(abaixo)
    return Pagina(linhas=linhas, tabela=tabela, confianca=confianca)


def extrair(
    caminho,
    coluna_e_texto: Callable[[int, int], bool],
    coluna_chave: Callable[[int], int | None] = lambda total: None,
    dpi: int | None = None,
) -> Documento:
    dpi = dpi or settings.IMPORTACAO_OCR_DPI
    documento = Documento(metodo="OCR")
    try:
        pdf = pdfium.PdfDocument(caminho)
    except pdfium.PdfiumError as erro:  # pragma: no cover - o arquivo já foi verificado antes
        raise ErroDeLeitura("Não foi possível abrir o PDF.") from erro
    try:
        for pagina in pdf:
            imagem = pagina.render(scale=dpi / 72, grayscale=True).to_pil().convert("L")
            documento.paginas.append(ler_pagina(imagem, coluna_e_texto, coluna_chave))
    except pytesseract.TesseractNotFoundError as erro:
        raise ErroDeLeitura(
            "O leitor de PDF escaneado (Tesseract) não está disponível no servidor. Avise a administração."
        ) from erro
    finally:
        pdf.close()
    return documento
