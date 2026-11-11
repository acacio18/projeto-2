"""Boletins simulados no mesmo modelo do boletim de exemplo do SUAP, para testes e demonstração.

O PDF original (`docs/referencias/boletins/exemplo_boletins.pdf`) é usado como molde: só os valores
das células de notas, faltas, frequência e situação, a linha "Diário:" e as "Aulas Ministradas" são
trocados, na mesma fonte (Helvetica 10) e na mesma posição. Cabeçalho, logos, grade e rodapé ficam
idênticos. Os alunos (nomes fictícios do boletim de exemplo) são os mesmos em todas as disciplinas,
como numa turma de verdade.

Séries geradas por disciplina:
- até o 1º, 2º e 3º bimestres e completo: cada uma acumula as anteriores (o 3º traz o 1º e o 2º);
- até o 1º, 2º e 3º bimestres com notas faltando: alguns alunos ficam sem nota ("-") em uma etapa.

Uso:
    .venv\\Scripts\\python -m tests.apoio.boletins_simulados --saida docs\\referencias\\boletins\\simulados
"""

import argparse
import copy
import ctypes
import random
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as raw

from tests.apoio.boletins import BOLETIM_EXEMPLO, carregar_gabarito

# Limites das colunas da tabela no molde (iguais nas duas páginas), em pontos.
COLUNAS_X = [
    15.7, 41.8, 114.6, 348.8, 395.7, 442.5, 494.6, 520.6, 546.7, 572.7,
    598.8, 624.8, 650.9, 677.0, 703.1, 729.1, 755.2, 781.2, 828.0,
]  # fmt: skip
PRIMEIRA_COLUNA_TROCADA = 3  # #, Matrícula e Nome ficam como estão

# Alunos (pela ordem no boletim) que ficam sem nota nas séries "com notas faltando": ordem → etapas.
NOTAS_FALTANDO = {3: {1}, 8: {2}, 12: {1, 3}, 20: {3}, 27: {2}}


@dataclass(frozen=True)
class Disciplina:
    diario: str
    codigo: str
    nome: str
    horas: int
    aulas: int
    ajuste: int = 0  # soma às notas de Análise e Projeto de Sistema, para variar o desempenho
    semente: int = 0

    @property
    def arquivo(self) -> str:
        simples = self.nome.lower().translate(str.maketrans("áâãàéêíóôõúç", "aaaaeeiooouc"))
        return f"{self.diario}_{'-'.join(simples.split())}"


ORIGINAL = Disciplina("70764", "TIN.0054", "Análise e Projeto de Sistema", 67, 80)
DISCIPLINAS = [
    ORIGINAL,
    Disciplina("70765", "TIN.0055", "Programação para Web", 67, 80, ajuste=4, semente=11),
    Disciplina("70768", "TIN.0052", "Banco de Dados", 67, 80, ajuste=-6, semente=12),
    Disciplina("70771", "TIN.0031", "Matemática III", 133, 160, ajuste=-14, semente=13),
]


def _inteiro(valor: Decimal) -> int:
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))  # como o SUAP (PRC-01)


def _frequencia(aulas: int, faltas: int) -> int:
    return _inteiro(Decimal(aulas - faltas) * 100 / aulas)


# --- Dados -------------------------------------------------------------------------------------


def dados_completos(disciplina: Disciplina) -> dict:
    """Valores do boletim completo (4 bimestres), no formato do gabarito."""
    dados = carregar_gabarito()
    if disciplina == ORIGINAL:
        return dados
    rng = random.Random(disciplina.semente)  # nosec B311 - dados de teste, não é segurança
    escala = disciplina.aulas // 80  # faltas maiores onde há mais aulas
    d = dados["diario"]
    d.update(codigo=disciplina.diario, disciplina_codigo=disciplina.codigo, disciplina_nome=disciplina.nome)
    d.update(carga_horaria_horas=disciplina.horas, aulas_previstas=disciplina.aulas)
    d["texto"] = (
        f"{disciplina.diario} - {disciplina.codigo} - {disciplina.nome} - Médio "
        f"[{disciplina.horas} h/{disciplina.aulas} Aulas]"
    )
    dados["aulas_ministradas"] = {
        "texto": f"{disciplina.aulas} de {disciplina.aulas} Aulas",
        "ministradas": disciplina.aulas,
        "previstas": disciplina.aulas,
    }
    for aluno in dados["alunos"]:
        for etapa in aluno["etapas"]:
            if etapa["nota"] is not None:
                nota = etapa["nota"] + disciplina.ajuste + rng.randint(-12, 12)
                etapa["nota"] = max(0, min(100, nota))
            etapa["faltas"] = rng.choice([0, 0, 0, 2, 2, 4]) * escala if etapa["nota"] is not None else 0
        aluno["total_faltas"] = sum(e["faltas"] for e in aluno["etapas"])
        if aluno["situacao"] == "Cancelado":
            continue
        aluno["frequencia_percentual"] = _frequencia(disciplina.aulas, aluno["total_faltas"])
        media = _inteiro(Decimal(sum(e["nota"] for e in aluno["etapas"])) / 4)
        aluno["media_disciplina"] = media
        if media >= 70:
            aluno["avaliacao_final"] = {"nota": None, "faltas": 0}
            aluno["media_final"] = media
        else:
            final = rng.randint(15, 95)
            aluno["avaliacao_final"] = {"nota": final, "faltas": 0}
            aluno["media_final"] = _inteiro(Decimal(6 * media + 4 * final) / 10)  # Art. 91
        aprovado = media >= 70 or aluno["media_final"] >= 50
        aluno["situacao"] = "Aprovado" if aprovado else "Reprovado"
    return dados


def ate_o_bimestre(dados: dict, bimestre: int, faltando: dict[int, set[int]] | None = None) -> dict:
    """O mesmo boletim como estaria no fim do bimestre informado (as etapas seguintes ainda vazias)."""
    dados = copy.deepcopy(dados)
    faltando = faltando or {}
    previstas = dados["diario"]["aulas_previstas"]
    aulas = previstas * bimestre // 4
    dados["aulas_ministradas"] = {
        "texto": f"{aulas} de {previstas} Aulas",
        "ministradas": aulas,
        "previstas": previstas,
    }
    for aluno in dados["alunos"]:
        for etapa in aluno["etapas"]:
            if etapa["etapa"] > bimestre:
                etapa.update(nota=None, faltas=0)
            elif etapa["etapa"] in faltando.get(aluno["ordem"], ()):
                etapa["nota"] = None
        aluno["total_faltas"] = sum(e["faltas"] for e in aluno["etapas"])
        if bimestre == 4 and not faltando:
            continue
        aluno["media_disciplina"] = None
        aluno["avaliacao_final"] = {"nota": None, "faltas": 0}
        aluno["media_final"] = None
        if aluno["situacao"] != "Cancelado":
            aluno["situacao"] = "Cursando"
            aluno["frequencia_percentual"] = _frequencia(aulas, aluno["total_faltas"])
    return dados


# --- PDF ---------------------------------------------------------------------------------------


def _valores_da_linha(aluno: dict) -> list[str]:
    def texto(valor) -> str:
        return "-" if valor is None else str(valor)

    freq = aluno["frequencia_percentual"]
    valores = [str(aluno["total_faltas"]), "-" if freq is None else f"{freq}%", aluno["situacao"]]
    for etapa in aluno["etapas"]:
        valores += [texto(etapa["nota"]), str(etapa["faltas"])]
    final = aluno["avaliacao_final"]
    valores += [texto(aluno["media_disciplina"]), texto(final["nota"]), str(final["faltas"])]
    return valores + [texto(aluno["media_final"])]


class _Pagina:
    """Uma página do molde: lê os objetos de texto e troca o que estiver numa região."""

    def __init__(self, documento: pdfium.PdfDocument, pagina: pdfium.PdfPage, fonte):
        self.documento, self.pagina, self.fonte = documento, pagina, fonte
        textos = pagina.get_textpage()
        self.objetos = []
        for objeto in pagina.get_objects():
            if objeto.type == raw.FPDF_PAGEOBJ_TEXT:
                esquerda, baixo, direita, cima = objeto.get_bounds()
                base = objeto.get_matrix().get()[5]
                self.objetos.append(
                    (objeto, esquerda, direita, (baixo + cima) / 2, base, self._texto(objeto, textos))
                )

    @staticmethod
    def _texto(objeto, textos) -> str:
        tamanho = raw.FPDFTextObj_GetText(objeto.raw, textos.raw, None, 0)
        memoria = (ctypes.c_ushort * tamanho)()
        raw.FPDFTextObj_GetText(objeto.raw, textos.raw, memoria, tamanho)
        return bytes(memoria).decode("utf-16-le").rstrip("\x00")

    def linhas_de_alunos(self) -> dict[int, float]:
        """Ordem do aluno → linha de base do texto, pela coluna "#"."""
        partes: dict[float, list[tuple[float, str]]] = {}
        for _, esquerda, direita, _, base, texto in self.objetos:
            if COLUNAS_X[0] <= (esquerda + direita) / 2 <= COLUNAS_X[1] and texto.strip():
                partes.setdefault(round(base, 1), []).append((esquerda, texto.strip()))
        linhas = {}
        for base, pedacos in partes.items():
            numero = "".join(t for _, t in sorted(pedacos))
            if numero.isdigit():
                linhas[int(numero)] = base
        return linhas

    def apagar(self, x0: float, x1: float, y0: float, y1: float) -> None:
        for item in list(self.objetos):
            objeto, esquerda, direita, meio, _, _ = item
            if x0 <= (esquerda + direita) / 2 <= x1 and y0 <= meio <= y1:
                self.pagina.remove_obj(objeto)
                objeto.close()
                self.objetos.remove(item)

    def escrever(self, texto: str, x: float, base: float, *, centro: float | None = None) -> None:
        objeto = raw.FPDFPageObj_CreateTextObj(self.documento.raw, self.fonte, ctypes.c_float(10))
        codificado = (texto + "\0").encode("utf-16-le")
        raw.FPDFText_SetText(objeto, (ctypes.c_ushort * (len(codificado) // 2)).from_buffer_copy(codificado))
        if centro is not None:
            esquerda, direita = ctypes.c_float(), ctypes.c_float()
            raw.FPDFPageObj_GetBounds(objeto, esquerda, ctypes.c_float(), direita, ctypes.c_float())
            x = centro - (direita.value - esquerda.value) / 2
        raw.FPDFPageObj_Transform(objeto, 1, 0, 0, 1, x, base)
        raw.FPDFPage_InsertObject(self.pagina.raw, objeto)

    def trocar_depois_do_rotulo(self, rotulo: str, texto: str, *, depois_de: float = 0) -> None:
        """Troca o valor que vem depois de um rótulo do cabeçalho ("Diário: ", "Aulas Ministradas: ")."""
        _, _, direita, _, base, _ = next(o for o in self.objetos if o[5].startswith(rotulo))
        valores = [o for o in self.objetos if abs(o[4] - base) < 1.5 and o[1] > max(direita, depois_de)]
        inicio = min(o[1] for o in valores if o[5].strip())
        self.apagar(inicio - 1, 842, base - 4, base + 10)
        self.escrever(texto, inicio - 0.4, base)


def gerar_pdf(dados: dict, destino: Path) -> Path:
    """Escreve o boletim com os valores de `dados` sobre o molde do boletim de exemplo."""
    documento = pdfium.PdfDocument(BOLETIM_EXEMPLO)
    fonte = raw.FPDFText_LoadStandardFont(documento.raw, b"Helvetica")
    alunos = {aluno["ordem"]: aluno for aluno in dados["alunos"]}
    for indice, pagina in enumerate(documento):
        molde = _Pagina(documento, pagina, fonte)
        if indice == 0:
            molde.trocar_depois_do_rotulo("Diário:", dados["diario"]["texto"])
            molde.trocar_depois_do_rotulo("Aulas Ministradas:", dados["aulas_ministradas"]["texto"])
        for ordem, base in molde.linhas_de_alunos().items():
            valores = _valores_da_linha(alunos[ordem])
            for coluna, valor in enumerate(valores, start=PRIMEIRA_COLUNA_TROCADA):
                x0, x1 = COLUNAS_X[coluna], COLUNAS_X[coluna + 1]
                molde.apagar(x0, x1, base - 4, base + 10)
                molde.escrever(valor, 0, base, centro=(x0 + x1) / 2)
        pagina.gen_content()
    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(destino)
    documento.close()
    return destino


def series() -> list[tuple[str, dict, int]]:
    """(nome do arquivo, dados, bimestre de corte) de todos os boletins simulados."""
    resultado = []
    for disciplina in DISCIPLINAS:
        completo = dados_completos(disciplina)
        for bimestre in (1, 2, 3, 4):
            sufixo = "completo" if bimestre == 4 else f"ate-o-{bimestre}o-bimestre"
            resultado.append(
                (f"{disciplina.arquivo}_{sufixo}.pdf", ate_o_bimestre(completo, bimestre), bimestre)
            )
        for bimestre in (1, 2, 3):
            nome = f"{disciplina.arquivo}_ate-o-{bimestre}o-bimestre_notas-faltando.pdf"
            resultado.append((nome, ate_o_bimestre(completo, bimestre, NOTAS_FALTANDO), bimestre))
    return resultado


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--saida", type=Path, required=True)
    argumentos = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    for nome, dados, _ in series():
        print(gerar_pdf(dados, argumentos.saida / nome))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
