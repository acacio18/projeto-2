# Evidência — E3: importação de boletins (IDs 3, 4, 5 e 18; parte do 13) — 10/11/2026

Autorizada pelo usuário em 10/11/2026 ("pode começar o próximo passo, que é a etapa 3").

## O que foi feito

### Envio (ID 3)
- **Tela "Enviar boletins"** (`/importacoes/enviar/`): um ou vários PDFs, ou um ZIP, mais o bimestre de corte ("até qual bimestre as notas estão fechadas", PRC-17). Há botões de envio no painel, na lista de diários e no próprio diário.
- **Verificações antes de gravar** (`apps/importacao/arquivos.py`):
  - o conteúdo precisa começar com `%PDF-`; um JPG renomeado para `.pdf` é recusado;
  - até 10 MB por PDF e 100 MB por envio;
  - até 50 arquivos por envio, somando os PDFs soltos e os de dentro do ZIP.
- **ZIP:**
  - lê só os PDFs e ignora o resto, com o motivo de cada recusa;
  - ignora ZIP dentro de ZIP e arquivo criptografado;
  - protege contra *zip-bomb*: confere o tamanho declarado e também para de ler quando os bytes reais passam do limite.
- **Gravação:**
  - o arquivo vai para a pasta de mídia privada com nome aleatório;
  - o SHA-256 é guardado; um arquivo idêntico a outro já enviado é recusado com o link para o envio anterior;
  - cada envio gera o evento de auditoria `IMPORTACAO_RECEBIDA` (ID 13).
- **Limites configuráveis** em `config/settings/base.py`: `IMPORTACAO_TAMANHO_MAXIMO_MB`, `IMPORTACAO_MAXIMO_PAGINAS` (20), `IMPORTACAO_LOTE_MAXIMO_ARQUIVOS` e `IMPORTACAO_LOTE_MAXIMO_MB`.

### Leitor do boletim (IDs 4 e 5)
O pacote `apps/importacao/leitura/` foi escrito do zero, sem código do protótipo.
- **Texto primeiro** (`texto.py`, pdfplumber): a maior tabela de cada página e as linhas de texto. A tabela que continua na página 2 sem cabeçalho é emendada.
- **OCR quando não há texto** (`ocr.py`, pypdfium2 + Tesseract `por`). As etapas:
  1. renderiza a 300 dpi;
  2. corrige a orientação pelo OSD do Tesseract (página de lado ou de cabeça para baixo);
  3. corrige a inclinação, até ±3°, pela projeção das linhas;
  4. binariza (Otsu);
  5. localiza a grade da tabela pelas linhas horizontais e verticais. A caixa do título é descartada porque só tem as bordas laterais;
  6. apaga a grade e lê coluna por coluna. Nas colunas numéricas, o Tesseract só aceita dígitos, `-`, `%` e `,`, o que tirou as trocas 0→O e 1→l;
  7. detecta o traço de "ausente" pelos pixels da célula;
  8. marca a célula ilegível com "?", que vira erro bloqueante e nunca é lida como ausente.
- **Perfil do SUAP** (`perfil_suap.py`):
  - o cabeçalho é lido por rótulos (`Curso:`, `Diário:`, `Ano/Período Letivo:`, `Aulas Ministradas:`, emissão e professor), com expressões tolerantes aos erros típicos de OCR;
  - os códigos numéricos são corrigidos (O→0, T→7, I/l→1, S→5, B→8, Z→2);
  - as colunas são achadas pelos **sinônimos** do cabeçalho de duas linhas ("Matrícula/Matr.", "Nome/Aluno", "E1/1º Bim", "NAF/Avaliação Final"…), e por isso colunas reordenadas ou renomeadas são lidas;
  - no OCR, sem cabeçalho legível, vale a ordem padrão do boletim.
- **Saída:** o mesmo formato do gabarito (`"esquema": 1`) que o serviço de versões da E2 já recebia, mais o método (texto ou OCR), a confiança média do OCR e a versão do leitor (`VERSAO_LEITOR = "1.0"`).
- **PDF problemático:** os casos protegido por senha, corrompido, sem páginas, com mais de 20 páginas, sem tabela de alunos e Tesseract ausente viram falha com mensagem clara.

### Validação (`apps/importacao/validacao.py`)
- **Erros, que impedem a importação:**
  - cabeçalho sem curso, diário ou período;
  - nenhum aluno;
  - matrícula fora do padrão (PRC-09) ou repetida;
  - valor fora de 0 a 100 (Art. 54 §3);
  - célula ilegível no OCR.
- **Avisos, que o professor confere antes de confirmar:**
  - total de faltas diferente da soma das etapas;
  - % de frequência, MD e MFD que não batem com o recálculo (meio para o par, PRC-01; MFD pelo Art. 91);
  - numeração fora de sequência;
  - notas depois do bimestre de corte (um aviso só, com o total);
  - aulas ministradas acima das previstas.
- Alunos cancelados ficam fora da conferência das médias.

### Fila e acompanhamento
- **Django-Q2 com a fila no PostgreSQL** (`Q_CLUSTER` em `config/settings/base.py`):
  - a leitura é agendada só depois do commit do envio;
  - tempo limite de 5 min por leitura, uma tentativa;
  - o gancho `ao_terminar` marca como falha a tarefa que morreu sem terminar (tempo esgotado, processo derrubado).
  - O `scripts/dev.ps1` sobe o `qcluster` junto com o servidor.
- **Estados:** `RECEBIDA → PROCESSANDO → AGUARDANDO_CONFIRMACAO` (vai para a conferência no diário, da E2) ou `FALHOU`, com a explicação e o botão "Ler de novo" (só para quem enviou ou para o administrador). A falha gera o evento `IMPORTACAO_FALHOU`.
- **Acompanhamento:** a página da importação e a do lote se atualizam sozinhas (`static/js/acompanhar.js`, consulta a cada 2 s, sem código em linha). Quando a leitura termina, a página leva direto à conferência.
- **Relatório da leitura na conferência:** mostra o método e a confiança e, no OCR, o pedido "confira o código do diário e da disciplina e as notas com atenção", além da lista de avisos por aluno.

### Lote (ID 18)
- Cada envio de vários arquivos vira um `LoteImportacao` (migração `importacao/0002_lote`), e cada PDF é uma importação independente na fila. A página do lote mostra a situação de cada arquivo, os arquivos não recebidos e os motivos.
- **Lista "Envios de boletins"** (`/importacoes/`) com tudo o que a pessoa enviou ou pode ver (`escopo.importacoes_visiveis`).

### Medição da acurácia (tarefa 8)
- `tests/apoio/medir_leitor.py` compara o leitor com o gabarito campo a campo e gera `docs/evidencias/E3-acuracia-leitor.md`.
- Gerador de boletins sintéticos (`tests/apoio/boletim_sintetico.py`, ReportLab): colunas reordenadas, rótulos renomeados, PDF com senha e PDF sem cabeçalho.

## Resultado da medição (576 campos por caso)
| Caso | Acurácia | Cabeçalho |
|---|---|---|
| PDF do SUAP (texto) | **100%** | certo |
| Sintéticos: colunas reordenadas / rótulos renomeados | **100%** / **100%** | certo |
| Escaneado 300 dpi | **99,3%** | certo |
| Escaneado 150 dpi | **99,7%** | certo |
| Escaneado 300 dpi, inclinado 1,5° e com ruído | **99,3%** | certo |
| Escaneado 300 dpi, girado 90° | **98,8%** | certo |

Nos escaneados, os erros que sobram são dígitos trocados (ex.: MD 59 em vez de 55) ou uma letra errada num nome. Todo número errado medido fez a validação apontar algo naquele aluno: média que não fecha, numeração fora de sequência ou valor fora da faixa. Detalhes em `E3-acuracia-leitor.md`.

## Decisões e desvios
| Assunto | Decisão |
|---|---|
| Estados do plano (`EXTRAINDO`, `VALIDANDO`, `CONCLUIDO`) | Viraram `PROCESSANDO` (leitura e validação levam de 1 a 25 s e não precisam de estados separados) e `AGUARDANDO_CONFIRMACAO`/`CONFIRMADA`, que a E2 já tinha. |
| Coordenadas como alternativa à tabela | No PDF de texto, o pdfplumber achou a tabela em todos os casos; no OCR, a grade da tabela faz o papel das coordenadas. Os perfis de layout ficam no `perfil_suap.py`, e um novo layout real entra como outro perfil. |
| Recálculo das contas | Só gera **aviso**. Os valores do boletim são os oficiais (PRC-01), e o professor decide. |
| "Mínimo de 2 avaliações" (RN-18) e "MB × avaliações" (RN-02) | Não se aplicam: o boletim não traz as notas por avaliação (análise do boletim de exemplo). |
| OCR com confiança alta não dispensa conferência | A tela pede atenção aos códigos e às notas sempre que a leitura foi por OCR, porque um código lido errado criaria outro diário. |
| Fila em testes | `sync=True` nos testes comuns. O `test_fila_real.py` (marcador `fila`) sobe um `qcluster` de verdade em outro processo, no banco de teste, como no `dev.ps1`. |

## Defeitos encontrados e corrigidos
1. **OCR trocando dígitos por letras** ("0" lido como "O", "70764" como "TOT64"): leitura por coluna com lista de caracteres permitidos e correção dos códigos. A acurácia subiu de 70% para 91%.
2. **Traço de "ausente" não lido pelo Tesseract:** detecção pelos pixels da célula; a acurácia chegou a 99%.
3. **Caixa do título confundida com a tabela:** a grade agora é a maior sequência de faixas cortadas por várias linhas verticais.
4. **Linhas do cabeçalho da tabela atrapalhando o OCR dos dígitos:** só as linhas de alunos são lidas, a partir da primeira matrícula.
5. **Aluno com matrícula inválida sumia em silêncio:** a linha agora entra e vira erro de validação. Só o cabeçalho é descartado.
6. **Período e emissão não reconhecidos no OCR** (`Anol/lPeríodo`, emissão colada na legenda): expressões mais tolerantes.
7. **Telas** (revisão das capturas):
   - o menu passava da largura em 1024 px;
   - a hora do envio no lote estava em UTC (23:47 em vez de 20:47);
   - o plural aparecia como "boletim(ns)";
   - a mensagem de "não é PDF" falava em ".pdf" para um JPG;
   - a coluna da data estava desalinhada na lista de envios;
   - faltava espaço entre os avisos e os botões da conferência.

## Critérios de aceitação da E3 (plano, 07-tarefas-por-etapa)
| Critério | Resultado | Prova |
|---|---|---|
| 100% dos campos corretos nos PDFs digitais | OK | `test_boletim_de_exemplo_e_lido_sem_nenhum_erro`, `test_layouts_variados_pelos_sinonimos_do_cabecalho`, medição (3 casos a 100%) |
| ≥ 98% nos escaneados a 300 dpi | OK no boletim de exemplo (99,3%; 98,8% a 99,7% nas variações) | `test_ocr_le_o_boletim_escaneado_com_pelo_menos_98_por_cento` (4 variantes), medição |
| Nenhum dado gravado sem confirmação | OK | A leitura termina em `AGUARDANDO_CONFIRMACAO` (`test_envio_le_valida_e_deixa_aguardando_confirmacao`); só a confirmação torna a versão vigente (`test_professor_envia_o_boletim_e_confirma_as_notas`, no navegador) |
| Erro sempre explicado | OK | `test_pdfs_problematicos_falham_com_mensagem_clara`, `test_boletim_com_problema_falha_com_explicacao`, `test_erro_inesperado_vira_falha_generica`, `test_falha_mostra_explicacao_e_permite_ler_de_novo` |
| Inválidos: não PDF, corrompido, criptografado, vazio, 0 alunos | OK | `test_assinatura_do_pdf`, `test_pdf_corrompido`, `test_pdf_protegido_por_senha`, `test_pdf_sem_paginas`, `test_pdf_sem_tabela_de_alunos`, `test_cabecalho_incompleto_e_sem_alunos_sao_erros` |
| Matrícula inválida, aluno repetido, notas ausentes | OK | `test_matricula_invalida_ou_repetida_e_nota_fora_da_faixa`, `test_celula_ilegivel_do_ocr_vira_problema_e_nao_ausente` |
| Reimportação idêntica | OK | `test_mesmo_arquivo_nao_e_enviado_duas_vezes`, `test_varios_pdfs_soltos_com_repetido_e_falso` |
| Lote com um arquivo ruim | OK | `test_lote_com_um_arquivo_ruim_nao_afeta_os_outros`, `test_varios_arquivos_viram_um_lote` |
| ZIP e zip-bomb | OK | `test_zip_respeita_os_limites_de_quantidade_e_de_tamanho`, `test_zip_corrompido_falso_ou_grande`, `test_pdf_grande_declarado_no_zip_e_ignorado_sem_ler` |
| Escopo: ninguém vê o envio alheio | OK | `test_ninguem_ve_o_envio_alheio`, `test_diario_de_outro_professor_falha`, `test_importacoes_visiveis_por_perfil` |
| Fila de verdade (fora do modo síncrono) | OK | `test_qcluster_le_o_boletim_enviado` |
| **Aceite de negócio: ≥ 10 boletins reais anonimizados (PRC-08)** | **PENDENTE** | Depende do envio das amostras. Até lá, a medição usa só o boletim de exemplo e as variações dele. |

## Pre-Delivery Checklist da skill (telas novas)
Capturas em `docs/evidencias/E3-telas/` (15 imagens: enviar, lote, falha, conferência por OCR e por texto, lista de envios e leitura em andamento; de 375 a 1440 px, temas claro e escuro), revisadas uma a uma.

| Item | Situação | Como |
|---|---|---|
| Ícones SVG de um conjunto só, sem emoji | OK | 2 ícones Lucide novos (`upload`, `file-up`), mesma versão fixa; hashes em `docs/design/recursos-de-terceiros.md` (38 ícones) |
| `cursor: pointer` e hover sem deslocar o layout | OK | Botões e links seguem os componentes da E1 |
| Contraste nos dois temas | OK | Etiqueta de erro nova com tokens já existentes; `test_contraste.py` verde |
| Sem rolagem horizontal de 375 a 1440 px | OK | `test_telas_da_e3_sem_rolagem_horizontal` (envio e lista × 4 larguras), `test_sem_rolagem_horizontal_em_nenhuma_largura` (menu em 1024 px) e revisão das capturas a 375 px |
| Estado de carregamento e retorno ao usuário | OK | Indicador "carregando" com `aria-live`, situação atualizada sozinha, mensagem ao enviar, falha com próximo passo ("Enviar outro arquivo", "Ler de novo") |
| Movimento reduzido | OK | Com `prefers-reduced-motion`, a regra global da E1 desliga a animação do indicador |
| A cor não é o único indicador | OK | Etiquetas de situação com ícone e texto |
| Campos com rótulo e ajuda ligados | OK | `FormularioAcessivel`; o campo de arquivos aceita `.pdf,.zip` e explica os limites |

O botão do campo de arquivo ("Choose Files") é o controle nativo do navegador: aparece em inglês nas capturas porque o Chromium dos testes está em inglês. Num navegador em português, aparece "Escolher arquivos". O controle nativo foi mantido por ser o mais acessível.

## Verificações executadas
| Verificação | Resultado |
|---|---|
| `test.ps1` (ruff, formatação, bandit, pytest com cobertura, pip-audit) | 5 etapas OK; **465 passed, 1 skipped** (a rotina de capturas); cobertura **100%** (2514 linhas, 516 desvios) |
| Testes de OCR (marcador `ocr`) | 5 passed (cerca de 90 s) |
| Fila real (marcador `fila`) | 1 passed: o `qcluster` leu o boletim em cerca de 3 s |
| Testes no navegador (Chromium) | Todos verdes, inclusive envio → conferência → confirmação |
| `makemigrations --check` | Nenhuma mudança pendente |
| pip-audit | Nenhuma vulnerabilidade conhecida |

## Pendências da E3
- **Aceite de negócio (PRC-08):** pelo menos 10 boletins reais anonimizados, de turmas e disciplinas diferentes, incluindo reprovados, Avaliação Final, transferidos e pelo menos um escaneado de verdade. A meta de ≥ 98% no OCR foi medida só com o boletim de exemplo.
- Um layout novo que apareça nas amostras entra como novo perfil em `perfil_suap.py`, sem mudar o resto.

## Próximo passo (aguarda autorização)
- **E4: motor de regras e estatísticas** (IDs 7, 22, 23 e 24): regras do Regimento como funções puras em `dominio/regras` (MA, recuperação, AF necessária, MF e situação projetada), estatística descritiva, frequência, índice de recuperação e ranking.
