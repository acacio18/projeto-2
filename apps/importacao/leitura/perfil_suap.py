"""Perfil de layout: "Boletim de Notas do Diário" do SUAP (IFPB), como o boletim de exemplo de 2023/2025.

O perfil sabe onde fica cada informação e devolve os dados no formato do gabarito ("esquema": 1).
Um layout diferente que apareça (outro ano do SUAP, outro relatório) ganha outro perfil, sem mexer
no resto do leitor.

Colunas: localizadas pelo cabeçalho da tabela, por sinônimos (Matrícula/Matr., Nome/Aluno etc.), de
modo que a ordem das colunas pode mudar. A página 2 não repete o cabeçalho e usa o mapa da página 1.
Se o cabeçalho não for reconhecido (OCR ruidoso), vale a ordem padrão do SUAP, desde que o número de
colunas bata; caso contrário a leitura falha com uma explicação.
"""

import re
import unicodedata
from decimal import Decimal, InvalidOperation

from apps.importacao.leitura.modelo import ILEGIVEL, Documento

NOME = "SUAP – Boletim de Notas do Diário"

# Ordem padrão das 18 colunas no boletim do SUAP.
ORDEM_PADRAO = [
    "ordem",
    "matricula",
    "nome",
    "total_faltas",
    "frequencia",
    "situacao",
    "e1_nota",
    "e1_faltas",
    "e2_nota",
    "e2_faltas",
    "e3_nota",
    "e3_faltas",
    "e4_nota",
    "e4_faltas",
    "md",
    "naf_nota",
    "naf_faltas",
    "mfd",
]
CAMPOS_DE_TEXTO = {"nome", "situacao"}
OBRIGATORIOS = {"matricula", "nome"}

# Sinônimos dos rótulos de uma coluna simples (comparados sem acento, em minúsculas).
SINONIMOS = {
    "ordem": ["#", "no", "n", "ordem"],
    "matricula": ["matricula", "matr", "matr."],
    "nome": ["nome", "aluno", "estudante", "nome do aluno"],
    "total_faltas": ["t. faltas", "t.faltas", "total de faltas", "faltas", "total faltas"],
    "frequencia": ["% freq.", "% freq", "%freq.", "freq.", "freq", "frequencia", "% frequencia"],
    "situacao": ["situacao", "situacao no diario"],
    "md": ["md", "media", "media da disciplina"],
    "mfd": ["mfd/ conceito", "mfd/conceito", "mfd", "conceito", "media final", "mfd/"],
}
ETAPA = re.compile(r"^(?:e\s*([1-4])|([1-4])\s*o?\s*(?:bim|b)\b)")
AVALIACAO_FINAL = re.compile(r"^(?:naf|af|avaliacao final)\b")
MATRICULA_PROVAVEL = re.compile(r"^\d{8,}$")


def sem_acento(texto: str) -> str:
    normal = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normal if not unicodedata.combining(c)).lower().replace("º", "o").strip()


# --- Cabeçalho do boletim --------------------------------------------------------------------

CURSO = re.compile(r"Curso:\s*([0-9OoTIlSBZ]{2,})\s*-\s*(.+)", re.IGNORECASE)
DIARIO = re.compile(
    r"Di[áa]rio:\s*([0-9OoTIlSBZ]{3,})\s*-\s*([A-Za-z0-9.]+)\s*-\s*(.+?)\s*-\s*([^\[]+?)\s*\[\s*(\d+)\s*h\s*/\s*(\d+)\s*Aulas?\s*\]",
    re.IGNORECASE,
)
PERIODO = re.compile(r"Ano\S{0,3}Per[íi]odo\s+Letivo:\s*(\d{4})\s*/\s*(\d)\s*(\([^)]*\))?", re.IGNORECASE)
AULAS = re.compile(r"Aulas\s+Ministradas:\s*(\d+)\s*de\s*(\d+)\s*Aulas?", re.IGNORECASE)
EMISSAO = re.compile(r"([A-ZÀ-Ý][A-Za-zÀ-ÿ' -]*?\s\([A-Z]{2}\)),\s*(\d{2})/(\d{2})/(\d{4})")
# Confusões típicas do OCR em códigos numéricos (só aplicadas a códigos quase todos numéricos).
CONFUSOES_OCR = str.maketrans(
    {"O": "0", "o": "0", "T": "7", "I": "1", "l": "1", "S": "5", "B": "8", "Z": "2"}
)


def codigo_numerico(texto: str) -> str:
    return texto.translate(CONFUSOES_OCR)


def _procurar(linhas: list[str], padrao: re.Pattern):
    for linha in linhas:
        achado = padrao.search(linha)
        if achado:
            return achado
    return None


def ler_cabecalho(linhas: list[str]) -> dict:
    dados = {
        "curso": {"texto": "", "codigo": None, "nome": ""},
        "diario": {
            "texto": "",
            "codigo": None,
            "disciplina_codigo": None,
            "disciplina_nome": "",
            "nivel": "",
            "carga_horaria_horas": None,
            "aulas_previstas": None,
        },
        "periodo_letivo": {"texto": "", "ano": None, "periodo": None, "etapas": []},
        "aulas_ministradas": {"texto": "", "ministradas": None, "previstas": None},
        "emissao": {},
        "professor_principal": "",
    }
    if achado := _procurar(linhas, CURSO):
        codigo = codigo_numerico(achado[1])
        dados["curso"] = {
            "texto": f"{codigo} - {achado[2].strip()}",
            "codigo": codigo,
            "nome": achado[2].strip(),
        }
    if achado := _procurar(linhas, DIARIO):
        codigo = codigo_numerico(achado[1])
        dados["diario"] = {
            "texto": achado[0].split(":", 1)[1].strip().replace(achado[1], codigo, 1),
            "codigo": codigo,
            "disciplina_codigo": achado[2],
            "disciplina_nome": achado[3].strip(),
            "nivel": achado[4].strip(),
            "carga_horaria_horas": int(achado[5]),
            "aulas_previstas": int(achado[6]),
        }
    if achado := _procurar(linhas, PERIODO):
        etapas = sorted({int(n) for n in re.findall(r"([1-4])\s*[º°o]", achado[3] or "")})
        dados["periodo_letivo"] = {
            "texto": f"{achado[1]}/{achado[2]} {achado[3] or ''}".strip(),
            "ano": int(achado[1]),
            "periodo": int(achado[2]),
            "etapas": etapas or [1, 2, 3, 4],
        }
    if achado := _procurar(linhas, AULAS):
        dados["aulas_ministradas"] = {
            "texto": f"{achado[1]} de {achado[2]} Aulas",
            "ministradas": int(achado[1]),
            "previstas": int(achado[2]),
        }
    for indice, linha in enumerate(linhas):
        if achado := EMISSAO.search(linha):
            dados["emissao"] = {"local": achado[1], "data": f"{achado[4]}-{achado[3]}-{achado[2]}"}
            nomes = []
            for seguinte in linhas[indice + 1 :]:
                if "professor principal" in sem_acento(seguinte):
                    dados["professor_principal"] = " ".join(nomes)
                    break
                if ":" not in seguinte:  # a legenda ("MD: Média da Disciplina") se mistura ao nome
                    nomes.append(seguinte)
            break
    return dados


# --- Colunas da tabela -----------------------------------------------------------------------


def _rotulo_simples(rotulo: str) -> str | None:
    texto = sem_acento(rotulo)
    for campo, sinonimos in SINONIMOS.items():
        if texto in sinonimos:
            return campo
    return None


def mapear_colunas(cabecalho: list[list[str | None]]) -> dict[str, int] | None:
    """Mapa campo → índice da coluna, a partir das linhas de cabeçalho (com células mescladas = None)."""
    if not cabecalho:
        return None
    largura = max(len(linha) for linha in cabecalho)
    grupos: list[str] = []  # rótulo de cima de cada coluna, propagado nas células mescladas
    atual = ""
    for indice in range(largura):
        celula = cabecalho[0][indice] if indice < len(cabecalho[0]) else None
        if celula is not None:
            atual = celula
        grupos.append(atual)
    mapa: dict[str, int] = {}
    for indice in range(largura):
        de_cima = sem_acento(grupos[indice])
        de_baixo = (
            sem_acento(cabecalho[1][indice] or "")
            if len(cabecalho) > 1 and indice < len(cabecalho[1])
            else ""
        )
        tipo = {"n": "nota", "f": "faltas"}.get(de_baixo)
        if (etapa := ETAPA.match(de_cima)) and tipo:
            mapa[f"e{etapa[1] or etapa[2]}_{tipo}"] = indice
        elif AVALIACAO_FINAL.match(de_cima) and tipo:
            mapa[f"naf_{tipo}"] = indice
        elif campo := _rotulo_simples(grupos[indice]):
            mapa.setdefault(campo, indice)
    return mapa if set(mapa) >= OBRIGATORIOS else None


def _e_cabecalho(linha: list[str | None]) -> bool:
    return any(_rotulo_simples(c or "") == "matricula" for c in linha)


# --- Valores ---------------------------------------------------------------------------------


class Leitor:
    """Converte o texto das células e anota o que não pôde ser lido."""

    def __init__(self):
        self.ilegiveis: list[dict] = []

    def _anotar(self, ordem, campo, texto):
        self.ilegiveis.append({"ordem": ordem, "campo": campo, "texto": texto})

    def numero(self, texto: str | None, ordem, campo: str):
        """Nota, faltas ou %: "-" e vazio = ausente (None); "95%" → 95; "82,5" → 82.5."""
        texto = (texto or "").strip()
        if texto in {"", "-", "–", "—"}:
            return None
        limpo = texto.rstrip("%").replace(",", ".").strip()
        try:
            valor = Decimal(limpo)
        except InvalidOperation:
            self._anotar(ordem, campo, texto)
            return None
        return int(valor) if valor == valor.to_integral_value() else valor

    def inteiro(self, texto: str | None, ordem, campo: str, padrao=0):
        valor = self.numero(texto, ordem, campo)
        if valor is None:
            return padrao
        if not isinstance(valor, int):
            self._anotar(ordem, campo, texto)
            return padrao
        return valor


def _celula(linha: list[str | None], mapa: dict[str, int], campo: str) -> str:
    indice = mapa.get(campo)
    if indice is None or indice >= len(linha):
        return ""
    valor = linha[indice]
    return "" if valor is None else valor


def _aluno(linha, mapa, leitor: Leitor) -> dict:
    ordem_texto = _celula(linha, mapa, "ordem")
    ordem = leitor.numero(ordem_texto, ordem_texto or "?", "ordem")
    ref = ordem if isinstance(ordem, int) else ordem_texto or "?"
    for campo in ORDEM_PADRAO:
        if ILEGIVEL in _celula(linha, mapa, campo).split():
            leitor._anotar(ref, campo, ILEGIVEL)
    mfd_texto = _celula(linha, mapa, "mfd").strip()
    mfd_numerico = re.fullmatch(r"[\d.,]+|-|–|—|", mfd_texto)
    return {
        "ordem": ordem if isinstance(ordem, int) else None,
        "matricula": re.sub(r"\s+", "", _celula(linha, mapa, "matricula")),
        "nome": " ".join(_celula(linha, mapa, "nome").split()),
        "total_faltas": leitor.inteiro(_celula(linha, mapa, "total_faltas"), ref, "total_faltas"),
        "frequencia_percentual": leitor.numero(
            _celula(linha, mapa, "frequencia"), ref, "frequencia_percentual"
        ),
        "situacao": " ".join(_celula(linha, mapa, "situacao").split()),
        "etapas": [
            {
                "etapa": n,
                "nota": leitor.numero(_celula(linha, mapa, f"e{n}_nota"), ref, f"nota do {n}º bimestre"),
                "faltas": leitor.inteiro(
                    _celula(linha, mapa, f"e{n}_faltas"), ref, f"faltas do {n}º bimestre"
                ),
            }
            for n in range(1, 5)
        ],
        "media_disciplina": leitor.numero(_celula(linha, mapa, "md"), ref, "média da disciplina"),
        "avaliacao_final": {
            "nota": leitor.numero(_celula(linha, mapa, "naf_nota"), ref, "nota da avaliação final"),
            "faltas": leitor.inteiro(_celula(linha, mapa, "naf_faltas"), ref, "faltas da avaliação final"),
        },
        "media_final": leitor.numero(mfd_texto, ref, "média final") if mfd_numerico else mfd_texto,
    }


def _e_linha_de_aluno(linha, mapa) -> bool:
    """Linha de aluno: tem nome e um número de ordem ou algo que lembre matrícula.

    Uma matrícula inválida não faz a linha sumir: ela chega à validação, que aponta o erro.
    """
    matricula = re.sub(r"\s+", "", _celula(linha, mapa, "matricula"))
    ordem = _celula(linha, mapa, "ordem").strip()
    nome = _celula(linha, mapa, "nome").strip()
    if not nome or _e_cabecalho(linha):
        return False
    return bool(ordem.isdigit() or MATRICULA_PROVAVEL.match(matricula) or re.search(r"\d{5,}", matricula))


def interpretar(documento: Documento) -> tuple[dict, list[dict], list[str]]:
    """Devolve (dados no formato do gabarito, células ilegíveis, avisos de leitura)."""
    linhas_texto = [linha for pagina in documento.paginas for linha in pagina.linhas]
    dados = {"esquema": 1, **ler_cabecalho(linhas_texto), "alunos": []}
    avisos: list[str] = []
    leitor = Leitor()
    mapa = None
    for numero, pagina in enumerate(documento.paginas, start=1):
        tabela = pagina.tabela
        if not tabela:
            continue
        cabecalho_inicio = next((i for i, linha in enumerate(tabela) if _e_cabecalho(linha)), None)
        if cabecalho_inicio is not None:
            mapa = mapear_colunas(tabela[cabecalho_inicio : cabecalho_inicio + 2]) or mapa
        if mapa is None and len(tabela[0]) == len(ORDEM_PADRAO):
            mapa = {campo: i for i, campo in enumerate(ORDEM_PADRAO)}
            if documento.metodo != "OCR":  # no OCR o cabeçalho sai ruidoso e a ordem padrão é o esperado
                avisos.append(
                    f"Página {numero}: cabeçalho da tabela não reconhecido; usada a ordem padrão do SUAP."
                )
        if mapa is None:
            continue
        for linha in tabela:
            if _e_linha_de_aluno(linha, mapa):
                dados["alunos"].append(_aluno(linha, mapa, leitor))
    return dados, leitor.ilegiveis, avisos


def coluna_e_texto(indice: int, total: int) -> bool:
    """Para o OCR: quais colunas têm texto (as outras só números). Layout desconhecido: todas texto."""
    if total != len(ORDEM_PADRAO):
        return True
    return ORDEM_PADRAO[indice] in CAMPOS_DE_TEXTO


def coluna_chave(total: int) -> int | None:
    """Para o OCR: a coluna da matrícula, que marca onde começam os dados (layout padrão do SUAP)."""
    return ORDEM_PADRAO.index("matricula") if total == len(ORDEM_PADRAO) else None
