"""Gera boletins sintéticos em PDF (ReportLab), parecidos com o do SUAP, para testar o leitor.

Permite variar o que o boletim real de exemplo não varia: ordem e nomes das colunas, alunos com
problemas (matrícula inválida, repetida, nota fora da faixa), proteção por senha. Os dados seguem o
formato do gabarito ("esquema": 1).
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.importacao.leitura.perfil_suap import ORDEM_PADRAO

ROTULOS_PADRAO = {
    "ordem": "#",
    "matricula": "Matrícula",
    "nome": "Nome",
    "total_faltas": "T. Faltas",
    "frequencia": "% Freq.",
    "situacao": "Situação",
    "md": "MD",
    "mfd": "MFD/ Conceito",
}
GRUPOS_PADRAO = {"e1": "E1 (1º B)", "e2": "E2 (2º B)", "e3": "E3 (3º B)", "e4": "E4 (4º B)", "naf": "NAF"}


def _celula(valor, sufixo=""):
    return "-" if valor is None else f"{valor}{sufixo}"


def _valor(aluno: dict, campo: str) -> str:
    if campo.startswith("e") and campo[1].isdigit():
        etapa = aluno["etapas"][int(campo[1]) - 1]
        return _celula(etapa["nota"]) if campo.endswith("nota") else str(etapa["faltas"])
    simples = {
        "ordem": str(aluno["ordem"]),
        "matricula": aluno["matricula"],
        "nome": aluno["nome"],
        "total_faltas": str(aluno["total_faltas"]),
        "frequencia": _celula(aluno["frequencia_percentual"], "%"),
        "situacao": aluno["situacao"],
        "md": _celula(aluno["media_disciplina"]),
        "naf_nota": _celula(aluno["avaliacao_final"]["nota"]),
        "naf_faltas": str(aluno["avaliacao_final"]["faltas"]),
        "mfd": _celula(aluno["media_final"]),
    }
    return simples[campo]


def gerar(
    dados: dict,
    *,
    colunas: list[str] = ORDEM_PADRAO,
    rotulos: dict | None = None,
    grupos: dict | None = None,
    senha: str | None = None,
    com_cabecalho: bool = True,
) -> bytes:
    rotulos = {**ROTULOS_PADRAO, **(rotulos or {})}
    grupos = {**GRUPOS_PADRAO, **(grupos or {})}
    estilos = getSampleStyleSheet()
    elementos = []
    if com_cabecalho:
        for linha in [
            "BOLETIM DE NOTAS DO DIÁRIO",
            f"Curso: {dados['curso']['texto']}",
            f"Diário: {dados['diario']['texto']}",
            f"Ano/Período Letivo: {dados['periodo_letivo']['texto']} "
            f"Aulas Ministradas: {dados['aulas_ministradas']['texto']}",
        ]:
            elementos.append(Paragraph(linha, estilos["Normal"]))
        elementos.append(Spacer(1, 8))

    topo, baixo, estilo = (
        [],
        [],
        [("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("FONTSIZE", (0, 0), (-1, -1), 7)],
    )
    for indice, campo in enumerate(colunas):
        grupo = campo.split("_")[0] if campo.split("_")[0] in GRUPOS_PADRAO else None
        if grupo:
            primeiro = indice == 0 or not colunas[indice - 1].startswith(grupo + "_")
            topo.append(grupos[grupo] if primeiro else "")
            baixo.append("N" if campo.endswith("nota") else "F")
            if primeiro and indice + 1 < len(colunas) and colunas[indice + 1].startswith(grupo + "_"):
                estilo.append(("SPAN", (indice, 0), (indice + 1, 0)))
        else:
            topo.append(rotulos[campo])
            baixo.append("")
            estilo.append(("SPAN", (indice, 0), (indice, 1)))
    linhas = [topo, baixo] + [[_valor(aluno, campo) for campo in colunas] for aluno in dados["alunos"]]
    tabela = Table(linhas, repeatRows=0)
    tabela.setStyle(TableStyle(estilo))
    elementos.append(tabela)
    if dados.get("emissao"):
        ano, mes, dia = dados["emissao"]["data"].split("-")
        elementos.append(Spacer(1, 8))
        elementos.append(Paragraph(f"{dados['emissao']['local']}, {dia}/{mes}/{ano}", estilos["Normal"]))
        elementos.append(Paragraph(dados.get("professor_principal", ""), estilos["Normal"]))
        elementos.append(Paragraph("(Professor Principal)", estilos["Normal"]))

    saida = io.BytesIO()
    documento = SimpleDocTemplate(
        saida,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
        encrypt=StandardEncryption(senha, canPrint=1) if senha else None,
    )
    documento.build(elementos)
    return saida.getvalue()
