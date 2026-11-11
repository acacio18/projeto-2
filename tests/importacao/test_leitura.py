"""Leitor de boletins (IDs 4 e 5): texto do PDF, perfil do SUAP, layouts variados e OCR.

Critérios da E3: 100% dos campos corretos nos PDFs com texto; ≥ 98% nos escaneados a 300 dpi.
"""

import pytest
from PIL import Image

from apps.importacao.leitura import ErroDeLeitura, ler_boletim, ocr, perfil_suap
from apps.importacao.leitura.leitor import verificar_pdf
from apps.importacao.leitura.modelo import ILEGIVEL, Documento, Pagina
from apps.importacao.validacao import validar
from tests.apoio.boletim_sintetico import gerar
from tests.apoio.boletins import carregar_gabarito

CABECALHO = ["curso", "diario", "periodo_letivo", "aulas_ministradas"]


def _sem_pagina(aluno: dict) -> dict:
    return {chave: valor for chave, valor in aluno.items() if chave != "pagina"}


def _campos(aluno: dict) -> list:
    """Os 18 valores de uma linha do boletim, na ordem das colunas."""
    valores = [aluno["ordem"], aluno["matricula"], aluno["nome"], aluno["total_faltas"]]
    valores += [aluno["frequencia_percentual"], aluno["situacao"]]
    for etapa in aluno["etapas"]:
        valores += [etapa["nota"], etapa["faltas"]]
    valores += [aluno["media_disciplina"], aluno["avaliacao_final"]["nota"]]
    return valores + [aluno["avaliacao_final"]["faltas"], aluno["media_final"]]


def acuracia(lidos: list[dict], esperados: list[dict]) -> float:
    """Percentual de campos corretos (alunos casados pela posição; faltar aluno conta como erro)."""
    total = certos = 0
    for indice, esperado in enumerate(esperados):
        lido = _campos(lidos[indice]) if indice < len(lidos) else [None] * 18
        for a, b in zip(lido, _campos(esperado), strict=True):
            total += 1
            certos += a == b
    return 100 * certos / total


def _escrever(tmp_path, conteudo: bytes, nome="boletim.pdf"):
    caminho = tmp_path / nome
    caminho.write_bytes(conteudo)
    return caminho


# --- PDF com texto (o caso normal) ---------------------------------------------------------------


def test_boletim_de_exemplo_e_lido_sem_nenhum_erro(boletim_exemplo, gabarito_exemplo):
    leitura = ler_boletim(boletim_exemplo, usar_ocr=False)
    dados = leitura.dados
    assert (leitura.metodo, leitura.paginas, leitura.confianca, leitura.ilegiveis, leitura.avisos) == (
        "TEXTO",
        2,
        None,
        [],
        [],
    )
    for parte in CABECALHO:
        assert dados[parte] == {chave: gabarito_exemplo[parte][chave] for chave in dados[parte]}
    assert dados["emissao"] == gabarito_exemplo["emissao"]
    assert dados["professor_principal"] == gabarito_exemplo["professor_principal"]
    assert dados["alunos"] == [_sem_pagina(a) for a in gabarito_exemplo["alunos"]]
    assert acuracia(dados["alunos"], gabarito_exemplo["alunos"]) == 100
    problemas = validar(dados, bimestre_corte=4, padrao_matricula=r"^\d{12}$")
    assert problemas == []  # o boletim real fecha todas as contas


ORDEM_TROCADA = ["nome", "matricula", "ordem", *perfil_suap.ORDEM_PADRAO[3:]]


@pytest.mark.parametrize(
    "opcoes",
    [
        {},
        {"colunas": ORDEM_TROCADA},
        {
            "rotulos": {
                "nome": "Aluno",
                "matricula": "Matr.",
                "total_faltas": "Total de faltas",
                "frequencia": "Frequência",
            },
            "grupos": {
                "e1": "1º Bim",
                "e2": "2º Bim",
                "e3": "3º Bim",
                "e4": "4º Bim",
                "naf": "Avaliação Final",
            },
        },
    ],
    ids=["padrao", "colunas-reordenadas", "rotulos-renomeados"],
)
def test_layouts_variados_pelos_sinonimos_do_cabecalho(tmp_path, opcoes):
    gabarito = carregar_gabarito()
    leitura = ler_boletim(_escrever(tmp_path, gerar(gabarito, **opcoes)), usar_ocr=False)
    assert leitura.dados["alunos"] == [_sem_pagina(a) for a in gabarito["alunos"]]
    assert leitura.dados["diario"]["codigo"] == "70764"


def test_decimal_com_virgula_e_conceito(tmp_path):
    gabarito = carregar_gabarito()
    gabarito["alunos"] = gabarito["alunos"][:2]
    gabarito["alunos"][0]["etapas"][0]["nota"] = "82,5"
    gabarito["alunos"][1]["media_final"] = "Apto"
    leitura = ler_boletim(_escrever(tmp_path, gerar(gabarito)), usar_ocr=False)
    from decimal import Decimal

    assert leitura.dados["alunos"][0]["etapas"][0]["nota"] == Decimal("82.5")
    assert leitura.dados["alunos"][1]["media_final"] == "Apto"


def test_pdf_sem_tabela_de_alunos(tmp_path):
    gabarito = carregar_gabarito()
    gabarito["alunos"] = []
    caminho = _escrever(tmp_path, gerar(gabarito))
    with pytest.raises(ErroDeLeitura, match="Não encontrei a tabela de alunos"):
        ler_boletim(caminho, usar_ocr=False)


# --- Arquivos problemáticos ----------------------------------------------------------------------


def test_pdf_protegido_por_senha(tmp_path):
    caminho = _escrever(tmp_path, gerar(carregar_gabarito(), senha="segredo"))
    with pytest.raises(ErroDeLeitura, match="protegido por senha"):
        verificar_pdf(caminho)


@pytest.mark.parametrize(
    "conteudo", [b"%PDF-1.4 isto nao e um pdf de verdade", b"\x89PNG\r\n\x1a\n" + b"0" * 100]
)
def test_pdf_corrompido(tmp_path, conteudo):
    with pytest.raises(ErroDeLeitura, match="corrompido"):
        verificar_pdf(_escrever(tmp_path, conteudo))


def test_limite_de_paginas(tmp_path, settings, boletim_exemplo):
    settings.IMPORTACAO_MAXIMO_PAGINAS = 1
    with pytest.raises(ErroDeLeitura, match="limite é 1"):
        verificar_pdf(boletim_exemplo)


def test_pdf_sem_paginas(monkeypatch, tmp_path):
    class PdfVazio:
        def __len__(self):
            return 0

        def close(self):
            pass

    monkeypatch.setattr("apps.importacao.leitura.leitor.pdfium.PdfDocument", lambda caminho: PdfVazio())
    with pytest.raises(ErroDeLeitura, match="nenhuma página"):
        verificar_pdf(tmp_path / "qualquer.pdf")


# --- Perfil do SUAP (peças) ----------------------------------------------------------------------


def test_cabecalho_tolera_erros_tipicos_de_ocr():
    dados = perfil_suap.ler_cabecalho(
        [
            "Curso: 66l - Técnico em Informática",
            "Diário: TOT64 - TIN.0054 - Análise e Projeto de Sistema - Médio [67 h/80 Aulas]",
            "Anol/lPeríodo Letivo: 2023/1 (1º, 2º, 3º e 4º Bim.) Aulas Ministradas: 80 de 80 Aulas",
            "E1, E2, E3 e E4: Etapas 1,2,3e4 Itaporanga (PB), 03/04/2025",
            "Maria da Silva",
            "MD: Média da Disciplina",
            "(Professor Principal)",
        ]
    )
    assert (dados["curso"]["codigo"], dados["diario"]["codigo"]) == ("661", "70764")
    assert dados["diario"]["texto"].startswith("70764 - TIN.0054")
    assert (dados["periodo_letivo"]["ano"], dados["periodo_letivo"]["etapas"]) == (2023, [1, 2, 3, 4])
    assert dados["emissao"] == {"local": "Itaporanga (PB)", "data": "2025-04-03"}
    assert dados["professor_principal"] == "Maria da Silva"


def test_cabecalho_ausente_fica_vazio():
    dados = perfil_suap.ler_cabecalho(["qualquer coisa"])
    assert dados["diario"]["codigo"] is None
    assert dados["periodo_letivo"]["etapas"] == []


@pytest.mark.parametrize(
    ("texto", "esperado", "ilegivel"),
    [("95%", 95, False), ("82,5", "82.5", False), ("-", None, False), ("", None, False), ("abc", None, True)],
)
def test_conversao_de_valores(texto, esperado, ilegivel):
    leitor = perfil_suap.Leitor()
    valor = leitor.numero(texto, 1, "campo")
    assert (str(valor) if valor is not None else None) == (str(esperado) if esperado is not None else None)
    assert bool(leitor.ilegiveis) is ilegivel


def test_inteiro_recusa_decimal_e_usa_padrao():
    leitor = perfil_suap.Leitor()
    assert leitor.inteiro("2,5", 1, "faltas") == 0
    assert leitor.ilegiveis == [{"ordem": 1, "campo": "faltas", "texto": "2,5"}]


def test_celula_ilegivel_do_ocr_vira_problema_e_nao_ausente():
    linha = ["1", "201927621032", "Aluno", ILEGIVEL, "95%", "Aprovado"] + ["0"] * 12
    documento = Documento(paginas=[Pagina(linhas=[], tabela=[linha])], metodo="OCR")
    dados, ilegiveis, avisos = perfil_suap.interpretar(documento)
    assert {"ordem": 1, "campo": "total_faltas", "texto": ILEGIVEL} in ilegiveis
    assert avisos == []  # no OCR a ordem padrão de colunas é a esperada
    assert dados["alunos"][0]["total_faltas"] == 0


def test_cabecalho_nao_reconhecido_no_pdf_de_texto_avisa_e_usa_a_ordem_padrao():
    linha = ["1", "201927621032", "Aluno"] + ["0"] * 15
    documento = Documento(paginas=[Pagina(linhas=[], tabela=[["x"] * 18, linha])], metodo="TEXTO")
    dados, _, avisos = perfil_suap.interpretar(documento)
    assert len(dados["alunos"]) == 1
    assert "ordem padrão" in avisos[0]


def test_tabela_de_layout_desconhecido_e_ignorada():
    documento = Documento(
        paginas=[Pagina(linhas=[], tabela=[["a", "b"], ["1", "2"]]), Pagina(linhas=[], tabela=[])]
    )
    dados, _, _ = perfil_suap.interpretar(documento)
    assert dados["alunos"] == []


def test_mapa_de_colunas_exige_matricula_e_nome():
    assert perfil_suap.mapear_colunas([]) is None
    assert perfil_suap.mapear_colunas([["#", "Nome"], [None, None]]) is None


def test_tipos_de_coluna_para_o_ocr():
    assert perfil_suap.coluna_e_texto(2, 18)
    assert perfil_suap.coluna_e_texto(5, 18)
    assert not perfil_suap.coluna_e_texto(6, 18)
    assert perfil_suap.coluna_e_texto(0, 10)  # layout desconhecido: tudo como texto
    assert (perfil_suap.coluna_chave(18), perfil_suap.coluna_chave(10)) == (1, None)


def test_codigo_numerico_corrige_confusoes_do_ocr():
    assert perfil_suap.codigo_numerico("TOT64") == "70764"
    assert perfil_suap.codigo_numerico("66l") == "661"


# --- OCR (peças rápidas) --------------------------------------------------------------------------


def test_otsu_separa_tinta_e_fundo():
    import numpy as np

    imagem = np.array([[20] * 10 + [230] * 10] * 4, dtype=np.uint8)
    assert 20 <= ocr.limiar_otsu(imagem) < 230


def test_celula_vazia_traco_ou_ilegivel():
    import numpy as np

    vazia = np.zeros((40, 60), dtype=bool)
    assert ocr.classificar_celula_vazia(vazia) == ""
    traco = vazia.copy()
    traco[20:23, 20:40] = True
    assert ocr.classificar_celula_vazia(traco) == "-"
    borrao = vazia.copy()
    borrao[5:35, 20:40] = True
    assert ocr.classificar_celula_vazia(borrao) == ILEGIVEL


def test_pagina_sem_tabela_vira_so_texto(monkeypatch):
    monkeypatch.setattr(ocr, "ler_texto", lambda imagem: ["texto solto"])
    monkeypatch.setattr(ocr, "corrigir_orientacao", lambda imagem: (imagem, 0))
    pagina = ocr.ler_pagina(
        Image.new("L", (400, 300), 255), perfil_suap.coluna_e_texto, perfil_suap.coluna_chave
    )
    assert (pagina.linhas, pagina.tabela) == (["texto solto"], [])


def test_orientacao_sem_texto_suficiente_nao_gira():
    imagem = Image.new("L", (200, 200), 255)
    girada, rotacao = ocr.corrigir_orientacao(imagem)
    assert (rotacao, girada.size) == (0, (200, 200))


def test_tesseract_ausente_vira_erro_explicado(monkeypatch, settings, boletim_exemplo):
    settings.TESSERACT_CMD = r"C:\nao\existe\tesseract.exe"
    with pytest.raises(ErroDeLeitura, match="Tesseract"):
        ocr.extrair(boletim_exemplo, perfil_suap.coluna_e_texto, dpi=50)


# --- OCR nos boletins escaneados (lento: cerca de 20 s cada) -----------------------------------

_LEITURAS: dict[str, object] = {}


def _ler_digitalizado(boletim_digitalizado, variante):
    if variante not in _LEITURAS:
        _LEITURAS[variante] = ler_boletim(boletim_digitalizado(variante))
    return _LEITURAS[variante]


@pytest.mark.ocr
@pytest.mark.parametrize("variante", ["300dpi", "150dpi", "300dpi_inclinado", "300dpi_girado90"])
def test_ocr_le_o_boletim_escaneado_com_pelo_menos_98_por_cento(
    boletim_digitalizado, gabarito_exemplo, variante
):
    leitura = _ler_digitalizado(boletim_digitalizado, variante)
    assert leitura.metodo == "OCR"
    assert leitura.confianca is not None
    assert leitura.confianca > 70
    assert len(leitura.dados["alunos"]) == 32
    assert acuracia(leitura.dados["alunos"], gabarito_exemplo["alunos"]) >= 98
    # Códigos e números do cabeçalho têm de vir certos (são eles que localizam o diário). Nomes lidos
    # por OCR podem ter letras trocadas; o curso e a disciplina já cadastrados mantêm o nome certo.
    dados, esperado = leitura.dados, gabarito_exemplo
    assert dados["curso"]["codigo"] == esperado["curso"]["codigo"]
    for chave in ["codigo", "disciplina_codigo", "carga_horaria_horas", "aulas_previstas"]:
        assert dados["diario"][chave] == esperado["diario"][chave], chave
    for chave in ["ano", "periodo", "etapas"]:
        assert dados["periodo_letivo"][chave] == esperado["periodo_letivo"][chave], chave
    assert dados["aulas_ministradas"] == esperado["aulas_ministradas"]


@pytest.mark.ocr
def test_erros_de_ocr_sao_apontados_pela_validacao(boletim_digitalizado, gabarito_exemplo):
    """Todo aluno lido com algum número errado aparece em um aviso ou erro da validação."""
    leitura = _ler_digitalizado(boletim_digitalizado, "300dpi")
    problemas = validar(
        leitura.dados, bimestre_corte=4, padrao_matricula=r"^\d{12}$", ilegiveis=leitura.ilegiveis
    )
    apontados = " ".join(p.aluno for p in problemas)
    numeracao_avisada = any("numeração dos alunos" in p.mensagem for p in problemas)
    for lido, esperado in zip(leitura.dados["alunos"], gabarito_exemplo["alunos"], strict=True):
        if lido["ordem"] != esperado["ordem"]:
            assert numeracao_avisada, "número de ordem errado sem aviso de numeração"
        numeros_errados = [
            a != b
            for a, b in zip(_campos(lido)[1:], _campos(esperado)[1:], strict=True)
            if not isinstance(b, str)
        ]
        if any(numeros_errados):
            assert lido["nome"] in apontados, lido["nome"]


# --- Casos de borda ------------------------------------------------------------------------------


def test_layout_sem_a_coluna_md(tmp_path):
    gabarito = carregar_gabarito()
    colunas = [c for c in perfil_suap.ORDEM_PADRAO if c != "md"]
    leitura = ler_boletim(_escrever(tmp_path, gerar(gabarito, colunas=colunas)), usar_ocr=False)
    assert all(a["media_disciplina"] is None for a in leitura.dados["alunos"])
    assert leitura.dados["alunos"][0]["media_final"] == 75


def test_coluna_desconhecida_e_ignorada():
    mapa = perfil_suap.mapear_colunas([["Matrícula", "Nome", "Observação"], [None, None, None]])
    assert mapa == {"matricula": 0, "nome": 1}


def test_emissao_sem_professor():
    dados = perfil_suap.ler_cabecalho(["Itaporanga (PB), 03/04/2025", "Legenda: algo"])
    assert dados["emissao"] == {"local": "Itaporanga (PB)", "data": "2025-04-03"}
    assert dados["professor_principal"] == ""


def test_otsu_de_imagem_vazia():
    import numpy as np

    assert ocr.limiar_otsu(np.zeros((0, 0), dtype=np.uint8)) == 128


def _grade(linhas_y, colunas_x, altura=200, largura=400):
    import numpy as np

    tinta = np.zeros((altura, largura), dtype=bool)
    for y in linhas_y:
        tinta[y, 20:380] = True
    for x in colunas_x:
        tinta[linhas_y[0] : linhas_y[-1] + 1, x] = True
    return tinta


def test_grade_escolhe_a_maior_tabela_e_ignora_faixas_finas():
    import numpy as np

    tinta = _grade([10, 16, 40, 70, 100], [20, 100, 200, 379])
    tinta[10:17, :] = False
    tinta[10, 20:380] = True  # faixa fina (10 a 16) acima da tabela
    tinta[16, 20:380] = True
    for x in [20, 100, 200, 379]:
        tinta[16:101, x] = True
    tinta[[130, 160], 20:380] = True  # segunda tabela, menor, abaixo
    for x in [20, 150, 379]:
        tinta[130:161, x] = True
    ys, xs = ocr.localizar_grade(tinta)
    assert (ys[0], ys[-1]) == (16, 100)
    assert xs == [20, 100, 200, 379]
    assert ocr.localizar_grade(np.zeros((50, 400), dtype=bool)) == ([], [])
    so_horizontais = np.zeros((100, 400), dtype=bool)
    so_horizontais[[10, 50, 90], 20:380] = True
    assert ocr.localizar_grade(so_horizontais) == ([], [])


def test_ler_tabela_encaixa_palavras_nas_linhas(monkeypatch):
    tinta = _grade([10, 40, 70], [20, 200, 379])
    palavras = {20: [(25.0, "A", 90.0), (55.0, "B", -1.0), (5.0, "fora", 50.0)], 200: [(30.0, "1", 80.0)]}
    monkeypatch.setattr(ocr, "_ler_coluna", lambda tinta, ys, x0, x1, so_numeros, escala: palavras[x0])
    tabela, confianca = ocr.ler_tabela(tinta, [10, 40, 70], [20, 200, 379], lambda c, t: True)
    assert tabela == [["A", "1"], ["B", ""]]
    assert confianca == 85.0  # a confiança -1 (desconhecida) não entra na média


def test_texto_de_regiao_vazia_ou_minuscula():
    assert ocr.ler_texto(Image.new("L", (400, 5), 255)) == []
    assert ocr.ler_texto(Image.new("L", (400, 100), 255)) == []
    assert ocr._linha_da_posicao([10, 20], 50) is None


def test_ampliacao_para_baixa_resolucao():
    import numpy as np

    imagem = ocr._imagem(np.zeros((10, 20), dtype=bool), escala=2, borda=0)
    assert imagem.size == (40, 20)
