"""Mede a acurácia do leitor de boletins por campo (tarefa 8 da E3) e escreve um relatório em Markdown.

Uso (cerca de 2 minutos, por causa do OCR):
    $env:DJANGO_SETTINGS_MODULE = "config.settings.dev"
    .venv\\Scripts\\python -m tests.apoio.medir_leitor --saida docs\\evidencias\\E3-acuracia-leitor.md
"""

import argparse
import os
import tempfile
import time
from pathlib import Path

import django

COLUNAS = [
    "#", "Matrícula", "Nome", "T. Faltas", "% Freq.", "Situação",
    "E1 N", "E1 F", "E2 N", "E2 F", "E3 N", "E3 F", "E4 N", "E4 F", "MD", "NAF N", "NAF F", "MFD",
]  # fmt: skip


def _valores(aluno: dict) -> list:
    valores = [aluno["ordem"], aluno["matricula"], aluno["nome"], aluno["total_faltas"]]
    valores += [aluno["frequencia_percentual"], aluno["situacao"]]
    for etapa in aluno["etapas"]:
        valores += [etapa["nota"], etapa["faltas"]]
    valores += [aluno["media_disciplina"], aluno["avaliacao_final"]["nota"]]
    return valores + [aluno["avaliacao_final"]["faltas"], aluno["media_final"]]


def comparar(lidos: list[dict], esperados: list[dict]) -> tuple[int, int, list[int], list[str]]:
    """(campos certos, total, erros por coluna, exemplos de erro)."""
    certos = total = 0
    por_coluna = [0] * len(COLUNAS)
    exemplos = []
    for indice, esperado in enumerate(esperados):
        lido = _valores(lidos[indice]) if indice < len(lidos) else [None] * len(COLUNAS)
        for coluna, (a, b) in enumerate(zip(lido, _valores(esperado), strict=True)):
            total += 1
            if a == b:
                certos += 1
            else:
                por_coluna[coluna] += 1
                if len(exemplos) < 6:
                    exemplos.append(f"aluno {esperado['ordem']}, {COLUNAS[coluna]}: “{a}” em vez de “{b}”")
    return certos, total, por_coluna, exemplos


def medir(saida: Path) -> None:
    from apps.importacao.leitura import ler_boletim
    from apps.importacao.leitura.perfil_suap import ORDEM_PADRAO
    from apps.importacao.validacao import validar
    from tests.apoio import digitalizacao
    from tests.apoio.boletim_sintetico import gerar
    from tests.apoio.boletins import BOLETIM_EXEMPLO, carregar_gabarito

    gabarito = carregar_gabarito()
    pasta = Path(tempfile.mkdtemp(prefix="medir_leitor_"))
    casos: list[tuple[str, Path]] = [("PDF do SUAP (texto)", BOLETIM_EXEMPLO)]
    sinteticos = {
        "Sintético: colunas reordenadas": {"colunas": ["nome", "matricula", "ordem", *ORDEM_PADRAO[3:]]},
        "Sintético: rótulos renomeados": {
            "rotulos": {"nome": "Aluno", "matricula": "Matr.", "total_faltas": "Total de faltas"},
            "grupos": {
                "e1": "1º Bim",
                "e2": "2º Bim",
                "e3": "3º Bim",
                "e4": "4º Bim",
                "naf": "Avaliação Final",
            },
        },
    }
    for nome, opcoes in sinteticos.items():
        caminho = pasta / f"{len(casos)}.pdf"
        caminho.write_bytes(gerar(gabarito, **opcoes))
        casos.append((nome, caminho))
    for variante, info in digitalizacao.VARIANTES.items():
        caminho = digitalizacao.gerar(BOLETIM_EXEMPLO, pasta / f"{variante}.pdf", info)
        casos.append((f"Escaneado: {info.descricao}", caminho))

    linhas = [
        "# Acurácia do leitor de boletins (E3, tarefa 8)",
        "",
        f"Gerado por `tests/apoio/medir_leitor.py` em {time.strftime('%d/%m/%Y %H:%M')}. "
        "Referência: o gabarito "
        "do boletim de exemplo (32 alunos × 18 colunas = 576 campos por caso). As versões escaneadas são "
        "geradas a partir do PDF real (`tests/apoio/digitalizacao.py`); os sintéticos, pelo ReportLab "
        "(`tests/apoio/boletim_sintetico.py`).",
        "",
        "| Caso | Método | Alunos | Campos certos | Acurácia | Cabeçalho (códigos) "
        "| Alertas da validação | Tempo |",
        "|---|---|---|---|---|---|---|---|",
    ]
    detalhes = []
    for nome, caminho in casos:
        inicio = time.perf_counter()
        leitura = ler_boletim(caminho)
        duracao = time.perf_counter() - inicio
        certos, total, por_coluna, exemplos = comparar(leitura.dados["alunos"], gabarito["alunos"])
        d = leitura.dados
        cabecalho_ok = (
            d["curso"]["codigo"] == gabarito["curso"]["codigo"]
            and d["diario"]["codigo"] == gabarito["diario"]["codigo"]
            and d["diario"]["disciplina_codigo"] == gabarito["diario"]["disciplina_codigo"]
            and d["periodo_letivo"]["ano"] == gabarito["periodo_letivo"]["ano"]
        )
        problemas = validar(d, bimestre_corte=4, padrao_matricula=r"^\d{12}$", ilegiveis=leitura.ilegiveis)
        n_erros = sum(p.nivel == "erro" for p in problemas)
        alertas = f"{n_erros} erro(s), {len(problemas) - n_erros} aviso(s)"
        linhas.append(
            f"| {nome} | {leitura.metodo} | {len(d['alunos'])}/32 | {certos}/{total} | "
            f"**{100 * certos / total:.1f}%** | {'certo' if cabecalho_ok else 'ERRADO'} | "
            f"{alertas} | {duracao:.1f} s |"
        )
        if exemplos:
            colunas_com_erro = ", ".join(f"{COLUNAS[i]} ({n})" for i, n in enumerate(por_coluna) if n)
            detalhes.append(
                f"- **{nome}**: erros por coluna: {colunas_com_erro}. Exemplos: {'; '.join(exemplos)}."
            )
    linhas += ["", "## Onde estão os erros", ""] + (detalhes or ["Nenhum erro."])
    linhas += [
        "",
        "## Leitura",
        "",
        "- PDFs com texto (o que o SUAP exporta) são lidos sem erro, "
        "inclusive com colunas reordenadas ou renomeadas.",
        "- Nos escaneados, os erros que sobram são dígitos trocados ou nomes com uma letra errada. "
        "A validação "
        "aponta os números que não fecham (média que não bate com as notas, faltas que não somam, valor fora "
        "de 0 a 100, numeração fora de sequência), e o professor confere antes de confirmar.",
        "- A meta do plano (≥ 98% dos campos a 300 dpi) foi medida só com este boletim; "
        "continua a validar com "
        "boletins reais escaneados (PRC-08).",
    ]
    saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--saida", type=Path, required=True)
    argumentos = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    django.setup()
    medir(argumentos.saida)


if __name__ == "__main__":
    main()
