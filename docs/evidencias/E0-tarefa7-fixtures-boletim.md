# Evidência — E0, tarefa 7: boletins de teste (04/11/2026)

Autorizada pelo usuário em 04/11/2026 ("agora pode começar o próximo passo").

## O que foi feito
- **Gabarito** `tests/fixtures/boletins/exemplo_boletins.gabarito.json`: transcrição manual, feita a partir da imagem das páginas de `docs/referencias/boletins/exemplo_boletins.pdf`. Inclui:
  - o cabeçalho completo (instituição, curso, diário com disciplina e carga horária, período letivo, aulas ministradas, emissão e professor);
  - os 32 alunos com todas as colunas (`#`, matrícula, nome, T. Faltas, % Freq., situação, N e F das etapas 1 a 4, MD, NAF N e F, MFD), com `null` onde o boletim tem `-`;
  - a lista de peculiaridades que o leitor precisa tolerar: título sem espaços, `Telefone: None`, tabela da página 2 sem cabeçalho, nomes com minúsculas e acentos, e cancelados com notas parciais.
- **Versões digitalizadas** (só imagem, sem camada de texto), geradas por `tests/apoio/digitalizacao.py` com pypdfium2, Pillow e numpy:
  - `300dpi`: escaneamento limpo;
  - `150dpi`: baixa resolução;
  - `300dpi_inclinado`: 1,5° de inclinação e ruído gaussiano σ = 8 com semente fixa;
  - `300dpi_girado90`: página de lado.

  Elas não são versionadas, porque têm de 0,5 a 2,5 MB e o pre-commit barra arquivos acima de 1 MB. Como a geração é determinística, os testes as recriam numa pasta temporária, uma vez por sessão. Há também uma linha de comando para gerá-las e conferi-las à mão: `python -m tests.apoio.digitalizacao --saida pasta`.
- **Fixtures do pytest** em `tests/conftest.py`: `boletim_exemplo` (caminho do PDF), `gabarito_exemplo` (relido a cada teste, então nenhum teste contamina outro) e `boletim_digitalizado(variante)`.
- Documentação em `tests/fixtures/boletins/README.md`. O doc 15 do planejamento e o CLAUDE.md foram atualizados.
- **Ajuste em relação ao plano:** o plano original previa um gerador de boletins sintéticos com ReportLab, porque na época não havia boletim real. Como o usuário forneceu o boletim de exemplo (doc 15, fato 9), esta tarefa usa o PDF real. Boletins sintéticos com variações de layout e casos de borda (colunas reordenadas, matrícula inválida, aluno duplicado, PDF corrompido) serão criados na E3, junto com os testes do leitor que os usam.

## Como o gabarito é conferido (tests/apoio/test_gabarito_exemplo.py)
| Conferência | Como |
|---|---|
| Arquivo certo | o SHA-256 do PDF é igual ao registrado no gabarito (`849aaec3…d449`) |
| Cabeçalho | cada campo aparece literalmente na camada de texto, e os campos estruturados (códigos, CH, ano/período, etapas) remontam o texto original |
| 32 linhas de aluno | cada linha montada a partir do gabarito existe na página certa da camada de texto (pdfplumber), e o PDF não tem linha de aluno a mais |
| Contas | faltas por etapa + faltas da AF = T. Faltas; % Freq. = (80 − faltas)/80 e MD = média das 4 notas, ambas arredondadas com meio para o par; MFD = MD ou (6·MD + 4·NAF)/10; cancelados sem % Freq., MD e MFD |
| PRC-01 | a aluna 4 soma 330 (média 82,5) e tem MD 82: meio para o par, não para cima |

**Os testes detectam erros:** um nome trocado (Felix → Feliz) e uma MD alterada (61 → 62) foram plantados de propósito, e 3 testes falharam. Depois o gabarito foi regenerado e voltou a passar.

## Linha de base do OCR (referência para a E3, não é critério desta tarefa)
Experimento com o Tesseract `por`, sem pré-processamento e com o modo de página padrão. A métrica é quantas das 32 matrículas aparecem corretas no texto reconhecido:

| Variante | Matrículas corretas |
|---|---|
| 150dpi | 32/32 |
| 300dpi | 9/32 |
| 300dpi_inclinado | 0/32 |
| 300dpi_girado90 | 0/32 (sem correção de rotação) |

Uma tentativa simples, com binarização e `--psm 6`, piorou o 300dpi (2/32).

Na versão de 300 dpi, o Tesseract junta as bordas da tabela aos dígitos (`|201927621032|`, `[202127621040`), e o marca-d'água verde do fundo atrapalha as colunas da direita. A OSD detectou a rotação de 90° corretamente. Conclusão para a E3: o OCR precisa remover as linhas da tabela e o fundo antes do reconhecimento, além de corrigir a inclinação e a rotação. A meta de ≥ 98% dos campos a 300 dpi continua a validar.

## Verificações executadas
| Verificação | Resultado |
|---|---|
| `pytest tests/apoio` | 82 passed (gabarito: 2 × 32 testes por aluno + 8; digitalização: 10) |
| Gabarito com 2 erros plantados | 3 failed (linhas dos alunos 9 e 17, contas do aluno 9) |
| `python -m tests.apoio.digitalizacao --saida …` | 4 PDFs gerados (524 KB a 2.522 KB); conferência visual da versão inclinada |
| `test.ps1` | 5 etapas OK, **93 passed**, cobertura 100% (apps/config/dominio), pip-audit sem vulnerabilidades, código 0 |
| `pre-commit run --all-files` | 10 ganchos Passed |

## Próxima tarefa da E0 (aguarda autorização)
- Tarefa 8: CI no GitHub Actions (runner Windows).
