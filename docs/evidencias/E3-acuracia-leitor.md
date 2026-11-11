# Acurácia do leitor de boletins (E3, tarefa 8)

Gerado por `tests/apoio/medir_leitor.py` em 10/11/2026 20:30. Referência: o gabarito do boletim de exemplo (32 alunos × 18 colunas = 576 campos por caso). As versões escaneadas são geradas a partir do PDF real (`tests/apoio/digitalizacao.py`); os sintéticos, pelo ReportLab (`tests/apoio/boletim_sintetico.py`).

| Caso | Método | Alunos | Campos certos | Acurácia | Cabeçalho (códigos) | Alertas da validação | Tempo |
|---|---|---|---|---|---|---|---|
| PDF do SUAP (texto) | TEXTO | 32/32 | 576/576 | **100.0%** | certo | 0 erro(s), 0 aviso(s) | 0.9 s |
| Sintético: colunas reordenadas | TEXTO | 32/32 | 576/576 | **100.0%** | certo | 0 erro(s), 0 aviso(s) | 0.2 s |
| Sintético: rótulos renomeados | TEXTO | 32/32 | 576/576 | **100.0%** | certo | 0 erro(s), 0 aviso(s) | 0.2 s |
| Escaneado: 300 dpi, tons de cinza, sem distorção | OCR | 32/32 | 572/576 | **99.3%** | certo | 0 erro(s), 4 aviso(s) | 20.2 s |
| Escaneado: 150 dpi (baixa resolução) | OCR | 32/32 | 574/576 | **99.7%** | certo | 0 erro(s), 1 aviso(s) | 20.3 s |
| Escaneado: 300 dpi, inclinado 1,5° e com ruído de scanner | OCR | 32/32 | 572/576 | **99.3%** | certo | 0 erro(s), 3 aviso(s) | 26.4 s |
| Escaneado: 300 dpi, página girada 90° (colocada de lado no scanner) | OCR | 32/32 | 569/576 | **98.8%** | certo | 2 erro(s), 5 aviso(s) | 21.4 s |

## Onde estão os erros

- **Escaneado: 300 dpi, tons de cinza, sem distorção**: erros por coluna: # (2), MD (1), NAF N (1). Exemplos: aluno 9, NAF N: “39” em vez de “35”; aluno 11, #: “1” em vez de “11”; aluno 13, #: “183” em vez de “13”; aluno 15, MD: “59” em vez de “55”.
- **Escaneado: 150 dpi (baixa resolução)**: erros por coluna: # (1), Nome (1). Exemplos: aluno 11, #: “1” em vez de “11”; aluno 20, Nome: “Magnus Carisen” em vez de “Magnus Carlsen”.
- **Escaneado: 300 dpi, inclinado 1,5° e com ruído de scanner**: erros por coluna: Nome (2), E3 N (1), MD (1). Exemplos: aluno 9, E3 N: “1” em vez de “75”; aluno 15, MD: “59” em vez de “55”; aluno 19, Nome: “Lohane veKkanandre sthephany” em vez de “Lohane vekanandre sthephany”; aluno 20, Nome: “Magnus Carilsen” em vez de “Magnus Carlsen”.
- **Escaneado: 300 dpi, página girada 90° (colocada de lado no scanner)**: erros por coluna: # (1), Nome (1), E3 N (1), MD (1), NAF N (1), MFD (2). Exemplos: aluno 1, MFD: “175” em vez de “75”; aluno 9, E3 N: “15” em vez de “75”; aluno 9, NAF N: “39” em vez de “35”; aluno 11, #: “1” em vez de “11”; aluno 15, MD: “59” em vez de “55”; aluno 19, Nome: “Lohane veKkanandre sthephany” em vez de “Lohane vekanandre sthephany”.

## Leitura

- PDFs com texto (o que o SUAP exporta) são lidos sem erro, inclusive com colunas reordenadas ou renomeadas.
- Nos escaneados, os erros que sobram são dígitos trocados ou nomes com uma letra errada. A validação aponta os números que não fecham (média que não bate com as notas, faltas que não somam, valor fora de 0 a 100, numeração fora de sequência), e o professor confere antes de confirmar.
- A meta do plano (≥ 98% dos campos a 300 dpi) foi medida só com este boletim; continua a validar com boletins reais escaneados (PRC-08).
