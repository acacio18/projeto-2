> Parte do Planejamento SUAP V2. Índice: [README.md](README.md)

# 15. Análise do boletim de exemplo (resolve parcialmente a PRC-08)

Arquivo: `C:\Users\Pichau\Downloads\exemplo_boletins.pdf` (182 KB, 2 páginas, **PDF com camada de texto**, não digitalizado). É um "BOLETIM DE NOTAS DO DIÁRIO" emitido pelo SUAP. Os repositórios do protótipo foram consultados **apenas** para procurar boletins de exemplo: o público (`phmferreira/leitordeboletim`, fork de `TiagoAmancio08/leitordeboletim`) não contém PDFs de boletim; o `phmferreira/projectMaths` é privado (HTTP 404 sem autenticação). Nenhum código do protótipo foi lido ou reaproveitado.

## Estrutura

**Cabeçalho institucional:** "INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DA PARAÍBA"; "Campus Itaporanga - Código INEP: 25128620"; endereço; CNPJ; título "BOLETIM DE NOTAS DO DIÁRIO" (na camada de texto sai sem espaços: `BOLETIMDENOTASDODIÁRIO`).

**Metadados (rótulo: valor):**
| Rótulo | Exemplo | Campos extraídos |
|---|---|---|
| Curso: | `661 - Técnico em Informática Integrado ao Ensino Médio - Itaporanga (CAMPUS ITAPORANGA)` | código do curso, nome, campus |
| Diário: | `70764 - TIN.0054 - Análise e Projeto de Sistema - Médio [67 h/80 Aulas]` | código do diário, código da disciplina, nome, nível, CH em horas, nº de aulas previstas |
| Ano/Período Letivo: | `2023/1 (1º, 2º, 3º e 4º Bim.)` | ano, período, etapas cobertas |
| Aulas Ministradas: | `80 de 80 Aulas` | ministradas / previstas |

**Tabela de alunos (cabeçalho em duas linhas):**
`#` · `Matrícula` · `Nome` · `T. Faltas` · `% Freq.` · `Situação` · `E1 (1º B)` [N, F] · `E2 (2º B)` [N, F] · `E3 (3º B)` [N, F] · `E4 (4º B)` [N, F] · `MD` · `NAF` [N, F] · `MFD/Conceito`

**Rodapé:** legenda (E1–E4 = Etapas; N = Nota da Etapa; F = Falta da Etapa; MD = Média da Disciplina; NAF = Nota da Avaliação Final; MFD = Média Final da Disciplina); local e data de emissão (`Itaporanga (PB), 03/04/2025`); nome do "(Professor Principal)".

## Fatos observados que mudam o planejamento

| # | Observação | Impacto |
|---|---|---|
| 1 | Há 32 linhas, 2 páginas; a tabela continua na pág. 2 **sem repetir o cabeçalho** | O parser junta as linhas de todas as páginas, guardando o mapeamento de colunas da pág. 1 |
| 2 | Matrículas com 12 dígitos (ex.: `201927621032`) | Confirma a PRC-09 (padrão `^\d{12}$`) |
| 3 | `Situação` ∈ {Aprovado, Cancelado} nesta amostra; os cancelados têm `-` nas notas e em `% Freq.`, inclusive com notas parciais (aluno 30) | Cancelados ficam registrados, mas **fora** das estatísticas e do n válido; o valor `-` = ausente (não zero) |
| 4 | Faltas por etapa (F) somam `T. Faltas`; `% Freq.` = (ministradas − faltas)/ministradas, arredondado | Validação cruzada na importação; frequência disponível por diário (ver PRC-03) |
| 5 | **Não há** nota de recuperação bimestral separada nem notas de avaliações individuais; `N` é a nota da etapa já registrada | RN-02 e RN-18 (conferência ΣA/n, mínimo de 2 avaliações) **não são verificáveis pelo boletim**; RN-05 está embutida em N |
| 6 | `NAF` aparece só para quem fez a AF (MD 50, 61, 55 neste exemplo); MFD = (6·MD + 4·NAF)/10 confere | A situação "Avaliação Final" é observável; a fórmula do Art. 91 foi validada com dado real |
| 7 | MD e % Freq. são inteiros; o arredondamento é compatível com "meio para o par" (ver PRC-01 em [14](14-decisoes-pendencias.md)) | Valores do boletim = oficiais; recálculo só para conferência |
| 8 | Todas as 4 etapas vêm no mesmo PDF | Confirma a DIV-04: o "bimestre informado" no upload define o **corte** (PRC-17) |
| 9 | O arquivo tem camada de texto; o boletim digitalizado (OCR) continua sem amostra | Fixtures de OCR: rasterizar este PDF (150/300 dpi, rotação) |

## Consequência para o ID 24 (Índice de recuperação)

Como o boletim **não separa** a nota de recuperação bimestral (fato 5), a definição planejada (ganho da recuperação bimestral) não pode ser calculada só com o PDF. Proposta para validação:
- **Índice de recuperação final** (calculável): entre os alunos com NAF, % com MFD ≥ 50, mais o ganho médio (MFD − MD). Nesta amostra: 3 de 3 recuperados; ganhos +18, −10 e +16. O ganho negativo de Diego (MD 61 → MFD 51) é efeito da ponderação 6/4 e não significa piora do aluno, o que precisa ficar explicado na interface.
- **Índice bimestral** (opcional): % de alunos com N < 70 em uma etapa que alcançaram N ≥ 70 na etapa seguinte. É um indicador exploratório de evolução, não de recuperação formal.
- A recuperação bimestral formal fica pendente de outra fonte de dados (ex.: lançamento manual pelo professor), fora do escopo do PDF.

## Uso como fixture

Este PDF passa a ser o **fixture de referência nº 1** da Etapa 3, com o gabarito (32 alunos, todas as colunas) transcrito em JSON. O aceite da E3 continua exigindo mais boletins reais (outras turmas e disciplinas, alunos reprovados ou em situações diferentes, e um digitalizado). Em 25/10/2026 o usuário confirmou que **os nomes são fictícios** e autorizou versionar o PDF no repositório público. A cópia versionada está em `docs/referencias/boletins/exemplo_boletins.pdf` (SHA-256 `849AAEC3441C0400DF12A6D77FD307AD80B3FE4668FEDE4D00EEDFD63426D449`). Futuros boletins reais só devem ser versionados com a mesma confirmação (PRC-14).
