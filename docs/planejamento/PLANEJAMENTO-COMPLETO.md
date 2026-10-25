# Planejamento completo — SUAP V2 (análise estatística de boletins SUAP para docentes)

> Escrito para: equipe de desenvolvimento e orientadores do projeto (IFPB) que vão validar o plano antes da implementação.
> Data da análise: 23/10/2026. Nenhum código foi escrito ou executado. Nenhum teste foi executado.

## 0. Contexto e ação imediata após aprovação

**Por que este plano existe.** O TCC de 2025 (IFPB Campus Itaporanga) deixou um protótipo Django que lê um único boletim por vez, sem banco de dados, sem login e sem histórico. A Tabela de Funcionalidades define 32 requisitos para o SUAP V2. Eles devem ser implementados **com código novo, do zero**, respeitando o Regimento Didático dos Cursos Técnicos Integrados (IFPB, 2024).

**Decisões já tomadas pelo usuário (23/10/2026):**
| Decisão | Escolha |
|---|---|
| Stack | Django monolito modular: Python 3.12 + Django 5.2 LTS + DRF + PostgreSQL 16 + Django-Q2 (fila no próprio PostgreSQL) + Tesseract; frontend com templates Django + HTMX + Chart.js |
| Ambiente | **Instalação nativa no Windows** (corrigido pelo usuário em 23/10/2026; substitui Docker/WSL2): Python, PostgreSQL, Tesseract e Git instalados via winget; virtualenv `.venv`; PostgreSQL como serviço do Windows |

**Adequações técnicas decorrentes da instalação nativa no Windows:**
| Componente | Problema no Windows | Escolha |
|---|---|---|
| Fila assíncrona | Celery não tem suporte oficial no Windows desde a versão 4.0 | **Django-Q2** com broker ORM (PostgreSQL): sem Redis, com agendamento nativo (usado no backup) |
| Servidor WSGI | Gunicorn não roda no Windows | **Waitress** (puro Python); o código fica agnóstico ao servidor, então Gunicorn continua possível se a produção for Linux |
| PDF de relatórios | WeasyPrint exige GTK/Pango | **ReportLab** (wheel puro) + matplotlib para os gráficos |
| OCR | OCRmyPDF exige Ghostscript/qpdf | **pypdfium2** (wheel, renderiza páginas sem Poppler) + **pytesseract** + Tesseract UB-Mannheim com idioma `por` |
| Cache/sessões | Sem Redis | Sessões no banco; cache local em memória ou no banco |
| ID 20 "Dashboard do aluno" | Painel **sobre** um estudante, acessado apenas por Professor (das próprias turmas) e Coordenador (do curso). Não se cria perfil "Aluno". |
| Boletins reais | Ainda não há. O parser começa com fixtures sintéticos; a Etapa 3 só é aceita com amostras reais anonimizadas. |

**Ação imediata após aprovação (pedido do usuário: "salve o que estamos fazendo na pasta PROGRAMA SUAP"):**
1. Criar `C:\Users\Pichau\Downloads\PROGRAMA SUAP\docs\planejamento\` (hoje não existe, portanto não há risco de sobrescrita) e salvar este planejamento dividido em arquivos Markdown:
   `00-resumo-executivo.md`, `01-fontes.md`, `02-diagnostico.md`, `03-inventario-funcionalidades.md`, `04-regimento-regras-de-negocio.md`, `05-arquitetura.md`, `06-plano-etapas.md`, `07-tarefas-por-etapa.md`, `08-matriz-rastreabilidade.md`, `09-plano-de-testes.md`, `10-riscos-pendencias.md`, `11-estimativas.md`, `12-criterios-conclusao.md`, `13-checklist-cobertura.md` e um `README.md` com índice.
2. Registrar na memória do projeto as decisões acima e as pendências de regra (PRC).
3. **Não iniciar a Etapa 0** antes de o usuário validar o planejamento e responder às pendências bloqueadoras (seção 11).

---

## 1. Resumo executivo

O SUAP V2 será uma aplicação web em que o professor envia o PDF "Boletim de Notas do Diário" exportado pelo SUAP. O sistema extrai as notas (por texto ou OCR), guarda o resultado com histórico versionado, calcula indicadores estatísticos, aplica as regras do Regimento Didático (médias, recuperação, Avaliação Final, frequência) e apresenta painéis, alunos em risco, comparações, projeções de reprovação e recomendações pedagógicas. Também gera relatórios em PDF, Excel, CSV e JSON, expõe uma API REST documentada em Swagger, registra auditoria e será implantado em produção com HTTPS, backup e monitoramento.

O trabalho foi organizado em **11 etapas (E0–E10)**. Os 32 IDs da tabela estão alocados em etapas concretas; os IDs 15–32 ("Contínuo") não ficam adiados indefinidamente. Há **18 pendências de regra/decisão (PRC-01…PRC-18)** e **9 divergências (DIV-01…DIV-09)** que precisam de validação institucional. A principal pendência técnica é a falta de boletins reais para calibrar o parser.

Princípio orientador: o Regimento afirma que a avaliação é "processual, diagnóstica… com prevalência dos aspectos qualitativos" (Art. 51) e que as decisões finais cabem ao Conselho de Classe (Arts. 56, 89 §2, 92). Por isso o sistema **nunca registra resultado acadêmico oficial**: apresenta apenas "situação projetada", "estimativas" e "sugestões", sempre com o critério explicado.

## 2. Fontes efetivamente analisadas

| Prioridade | Documento | Local | Leitura |
|---|---|---|---|
| 1 | Tabela de Funcionalidades final.pdf (4 p.) | `C:\Users\Pichau\Downloads\` | Integral. 32 IDs (1–32). A pág. 4 tem texto corrompido na extração, mas a imagem da página foi conferida e o conteúdo dos IDs 11–14 está legível. |
| 2 | TCC_AUTOMACAO_NOTAS_SUAP.pdf (33 p.) | idem | Integral, incluindo figuras (planilha-protótipo, trechos de código, telas). |
| 3 | Regimento_didatico_-_integrado_-_2024.pdf (30 p.) | idem | Integral, incluindo o Anexo 01 (nota mínima na AF). |
| 4 | Pasta do projeto `PROGRAMA SUAP` | — | Inspecionada: contém apenas `.claude\skils\` (vazia). **Não há código-fonte.** |

Não foi possível verificar: (a) o **layout real do boletim SUAP**, pois nenhum PDF de boletim foi fornecido; só se conhece o cabeçalho visível na Fig. 5 do TCC ("Curso: 661 – Técnico em Informática Integrado…", "Diário: 70764 – TIN.0054 – Análise e Projeto de Sistema – Médio [67 h/80 Aulas]", "Ano/Período Letivo: 2023/1 (1º, 2º, 3º e 4º Bim.)", "Aulas Ministradas: 80 de 80"); (b) os regulamentos complementares citados no Art. 2º do Regimento (Conselho de Classe, Progressão Parcial etc.), que não foram fornecidos; (c) o código do protótipo do TCC, do qual há só capturas de tela (e que, de qualquer forma, não será reutilizado).

## 3. Diagnóstico técnico do código e do ambiente

**Código existente:** nenhum. A pasta `.claude\skils\` é configuração do ambiente do Claude Code, não código funcional; deve ser preservada e ignorada. Situação atual de todos os 32 IDs: **ausente**.

**Ambiente (verificado em 23/10/2026, somente leitura):**
| Item | Situação |
|---|---|
| SO | Windows 10 Pro 19045; i5-8500; 15,9 GB RAM; 56,6 GB livres em C: |
| Python | Não instalado (apenas o atalho da Microsoft Store) |
| Node, Git, Docker, PostgreSQL, Redis, Tesseract, Poppler | Não instalados |
| WSL | Só o stub; nenhuma distribuição instalada |
| Virtualização de firmware | Habilitada (permite WSL2 + Docker Desktop) |
| winget | Disponível |
| VS Code | Instalado |

**Consequência:** a Etapa 0 começa pela instalação nativa (winget) de Python 3.12, PostgreSQL 16, Tesseract (UB-Mannheim) com o idioma português e Git, o que exige a autorização do usuário porque altera o sistema. O atalho "python" da Microsoft Store deve ser desativado em *Aliases de execução do aplicativo*. Hardware e disco são suficientes para a stack nativa (sem Redis, Docker ou Poppler).

**O que o TCC informa sobre o sistema original (referência funcional, não código):** fluxo de upload de PDF + escolha do bimestre → pdfplumber → pandas (filtros: matrícula com 12 dígitos, sem "cancelado", sem células vazias) → média, mediana, desvio-padrão (`.std()` do pandas, ou seja, amostral), mínimo e máximo, faixas de desempenho → histograma, barras ordenadas e pizza → PDF com ReportLab. Limitações declaradas (TCC §5.4 e §6): dependência do layout, uma turma por envio, processamento síncrono, sem persistência nem histórico, poucos indicadores. Melhorias propostas (§5.5): persistência, Celery+Redis, API REST, dashboards, parser robusto com OCR de fallback, validação quantitativa do parser e do risco, privacidade (HTTPS, autenticação, anonimização). Todas essas melhorias estão cobertas por IDs da tabela.

## 4. Inventário completo das funcionalidades (tabela original)

| ID | Módulo | Funcionalidade | Usuários | Prior. | Etapa orig. |
|---|---|---|---|---|---|
| 1 | Infraestrutura | Login (e-mail institucional + senha; identifica perfil; sessão segura; painel por perfil) | Professor, Coordenador, Admin | Alta | 1 |
| 2 | Infraestrutura | Permissões (Professor: só suas turmas; Coordenador: todas as turmas do curso; Admin: tudo) | Admin | Alta | 1 |
| 3 | Importação | Upload PDF (professor envia boletim + informa bimestre; integridade; extração automática) | Professor | Alta | 2 |
| 4 | Importação | Parser Inteligente (tabelas, nomes, matrículas, disciplinas, notas; tolera pequenas variações) | Sistema | Alta | 2 |
| 5 | Importação | OCR (PDF digitalizado → texto antes da extração) | Sistema | Média | 2 |
| 6 | Dados | Banco de Dados (persistir histórico; consultas; comparação entre períodos) | Sistema | Alta | 3 |
| 7 | Estatísticas | Indicadores (média, mediana, moda, variância, desvio, mín., máx., quartis e outras) | Professor, Coordenador | Alta | 4 |
| 8 | Learning Analytics | Alunos em risco (classificar por nível de risco) | Professor, Coordenador | Alta | 5 |
| 9 | Learning Analytics | Comparações (turmas, disciplinas, bimestres, anos) | Professor, Coordenador | Alta | 5 |
| 10 | Dashboards | Painéis (gráficos, tabelas, indicadores atualizados em tempo real) | Professor, Coordenador, Admin | Alta | 6 |
| 11 | Relatórios | Exportações (PDF, Excel, CSV, JSON com estatísticas, gráficos e listas de alunos) | Professor | Alta | 7 |
| 12 | API | Integração (API REST para outras aplicações consultarem/enviarem dados) | Admin, Desenvolvedor | Média | 8 |
| 13 | Segurança | Logs/Auditoria (login, importação, relatórios, alterações cadastrais) | Admin | Alta | 9 |
| 14 | Deploy | Produção (servidor, banco, HTTPS, backup, monitoramento) | Admin | Alta | 10 |
| 15 | Funcionalidades | Cadastro de professores | Conforme perfil | Média | Contínuo |
| 16 | Funcionalidades | Cadastro de turmas | Conforme perfil | Média | Contínuo |
| 17 | Funcionalidades | Cadastro de disciplinas | Conforme perfil | Média | Contínuo |
| 18 | Funcionalidades | Processamento em lote | Conforme perfil | Média | Contínuo |
| 19 | Funcionalidades | Histórico | Conforme perfil | Média | Contínuo |
| 20 | Funcionalidades | Dashboard do aluno | Conforme perfil | Média | Contínuo |
| 21 | Funcionalidades | Dashboard da turma | Conforme perfil | Média | Contínuo |
| 22 | Funcionalidades | Ranking | Conforme perfil | Média | Contínuo |
| 23 | Funcionalidades | Frequência | Conforme perfil | Média | Contínuo |
| 24 | Funcionalidades | Índice de recuperação | Conforme perfil | Média | Contínuo |
| 25 | Funcionalidades | Predição de reprovação | Conforme perfil | Média | Contínuo |
| 26 | Funcionalidades | Recomendações pedagógicas | Conforme perfil | Média | Contínuo |
| 27 | Funcionalidades | Backup | Conforme perfil | Média | Contínuo |
| 28 | Funcionalidades | Swagger | Conforme perfil | Média | Contínuo |
| 29 | Funcionalidades | API REST | Conforme perfil | Média | Contínuo |
| 30 | Funcionalidades | Exportar Excel | Conforme perfil | Média | Contínuo |
| 31 | Funcionalidades | Exportar CSV | Conforme perfil | Média | Contínuo |
| 32 | Funcionalidades | Exportar JSON | Conforme perfil | Média | Contínuo |

A descrição dos IDs 15–32 na tabela é sempre "Implementar recurso descrito no TCC ou melhoria".

**Sobreposições (todas mantidas e rastreáveis, sem eliminar IDs):**
| Grupo | Organização técnica |
|---|---|
| 6 × 19 | ID 6 = camada de persistência versionada (modelo, migrações, integridade). ID 19 = funcionalidade visível ao usuário: histórico de importações, linha do tempo do aluno e da turma, comparação de versões. |
| 11 × 30/31/32 | ID 11 = módulo de relatórios e PDF completo. IDs 30/31/32 = exportadores de formato específicos e testados separadamente, que reutilizam o mesmo "conjunto de dados de relatório". |
| 12 × 28 × 29 | ID 29 = recursos REST (endpoints). ID 12 = integração externa (credenciais de cliente, escopos, escrita controlada). ID 28 = especificação OpenAPI + Swagger UI. |
| 14 × 27 | ID 27 = mecanismo de backup e restauração (rotina, criptografia, teste de restore). ID 14 = ambiente de produção que agenda e monitora esse backup. |
| 10 × 20 × 21 | ID 10 = infraestrutura de painéis e painéis gerais por perfil. ID 20 = painel de um estudante. ID 21 = painel de uma turma/diário. |
| 7 × 22 × 24 | ID 7 = estatística descritiva. ID 22 = ordenação/ranking. ID 24 = índice derivado da recuperação bimestral (Art. 63). |
| 8 × 25 × 26 | ID 8 = classificação de risco atual. ID 25 = projeção do resultado anual. ID 26 = sugestões vinculadas às duas anteriores. |

## 5. Regimento Didático (IFPB, 2024): regras de negócio identificadas

Legenda: **[OBR]** = regra institucional obrigatória; **[EXP]** = critério estatístico ou exploratório (não normativo); **[PRC]** = regra pendente de confirmação.

### 5.1 Regras com suporte no texto oficial

| Cód. | Referência | O que a norma determina (fiel) | IDs afetados | Consequência no sistema | Testes que comprovam |
|---|---|---|---|---|---|
| RN-01 [OBR] | Art. 54 §3 | Avaliações expressas em notas de 0 a 100 | 3, 4, 5, 7 | Validação rejeita ou sinaliza nota < 0 ou > 100; escala fixa 0–100 nos gráficos | Unitário: −1, 0, 100, 100.01, "abc" |
| RN-02 [OBR] | Art. 55 I | MB = ΣA / n (média aritmética das avaliações realizadas) | 4, 7, 24 | Se o boletim trouxer as notas por avaliação, recalcular a MB e conferir com a MB informada (divergência = alerta de qualidade); se trouxer só a MB, usá-la | Unitário com n = 2, 3, 5 |
| RN-03 [OBR] | Art. 55 II | MA = (MB1 + MB2 + MB3 + MB4) / 4 | 7, 8, 25 | MA só é "definitiva" com 4 MB; antes disso, existe só a MA parcial/projetada (RN-21) | Unitário; caso com MB ausente |
| RN-04 [OBR] | Art. 63 caput | Avaliação de recuperação ao fim de cada bimestre para quem não atingiu MB 70 | 8, 24, 26 | Marca "elegível à recuperação bimestral" quando MB < 70 | Limites: 69,99 / 70 / 70,01 |
| RN-05 [OBR] | Art. 63 §1 | Para registro, prevalece o maior valor entre a MB e a nota de recuperação | 4, 24 | Nota registrada = max(MB, Rec); a nota pré-recuperação é guardada para o índice de recuperação | Unitário: Rec < MB, Rec > MB, Rec ausente |
| RN-06 [OBR] | Art. 63 §2 | Perde o direito à recuperação quem faltou sem justificativa a qualquer avaliação do bimestre | 24, 26 | Informação ausente no boletim → apenas texto explicativo; o sistema não infere | Teste de UI: o aviso aparece |
| RN-07 [OBR] + PRC-05 | Art. 64 | Se > 30% da turma não alcançar rendimento satisfatório nas avaliações bimestrais, as causas devem ser diagnosticadas em Conselho de Classe | 8, 21, 26 | Alerta de turma quando a proporção de "não satisfatório" > 30% (estritamente maior) | 30% exato não dispara; 30,1% dispara; turma vazia não dispara |
| RN-08 [OBR] | Art. 88 | Aprovado: MA ≥ 70 em cada componente **e** frequência ≥ 75% da CH total prevista no ano | 8, 23, 25 | Situação projetada "Aprovado" | Matriz de casos MA × frequência |
| RN-09 [OBR] | Art. 89 caput | Vai à Avaliação Final quem tem frequência ≥ 75% e 40 < MA < 70 | 8, 25 | Situação projetada "Avaliação Final" | MA 40, 40,01, 69,99, 70 |
| RN-10 [OBR] | Art. 89 §1 + Anexo 01 | MA < 40 em até 3 componentes: tem direito à AF, respeitada a nota mínima do Anexo 01 (MA 69 → AF 22 … MA 17 → AF 100) | 8, 25, 26 | Calcula a "AF mínima necessária". Com MA < 17, a aprovação na AF é matematicamente impossível (MF máx < 50) | Tabela do Anexo inteira como teste parametrizado (MA 17–69) |
| RN-11 [OBR] | Art. 89 §2 | Quem não atinge a MA mínima para AF em até 6 componentes tem a situação deliberada pelo Conselho de Classe do 4º bimestre | 8, 25 | Rótulo "Depende do Conselho de Classe"; nunca "Reprovado" | Estudante com 4–6 componentes MA < 40 |
| RN-12 [OBR] | Art. 91 | MF = (6·MA + 4·AF) / 10; aprovado se MF ≥ 50 | 25 | Calcula MF quando a AF existe; AF necessária = ⌈(500 − 6·MA)/4⌉ (confere com o Anexo 01) | Conferência fórmula × Anexo 01 em todos os 53 pontos |
| RN-13 [OBR] | Art. 92 | Conselho de Classe Final para quem fez a AF e ficou com MF < 50 em até 3 componentes | 25 | Rótulo "Conselho de Classe Final" | 3 vs 4 componentes |
| RN-14 [OBR] | Art. 93 | Progressão Parcial: até 3 componentes em reprovação após AF e Conselho Final | 25, 26 | Rótulo informativo "Possível Progressão Parcial (decisão do Conselho)" | Casos limite |
| RN-15 [OBR] | Art. 94 I–V | Retenção: frequência < 75%; MA < 40 em mais de 3 componentes (salvo Art. 89 §2); MF < 50 em mais de 3; não realizar a AF; não aprovado nem com Progressão Parcial pelo Conselho Final | 8, 25 | "Risco de retenção" projetado (nunca resultado oficial) | Casos I–IV |
| RN-16 [OBR] + PRC-03/04 | Art. 77; Art. 94 §1 | Limite de 25% de faltas sobre a CH do período; faltas justificadas são desconsideradas na apuração da frequência para retenção | 23, 8, 25 | Frequência = 1 − faltas/CH; alerta quando a projeção de faltas ultrapassa 25% | 25% exato; CH zero; faltas > CH |
| RN-17 [OBR] | Art. 95 | Evadido: ausência não justificada > 25% da CH do período e/ou rendimento nulo em todos os componentes | 8, 23 | Rótulo "risco de evasão" (indicador; a classificação oficial é do SUAP) | Caso de rendimento nulo |
| RN-18 [OBR] | Art. 54 §8 | Mínimo de 2 avaliações por bimestre | 4 | Se o boletim trouxer as avaliações, menos de 2 = aviso de qualidade (não bloqueia) | n = 1 |
| RN-19 [OBR] | Art. 11; Art. 12 VI | Regime anual com bimestres | 3, 6, 9 | Bimestre ∈ {1, 2, 3, 4}; período = ano letivo | Bimestre 0 e 5 são rejeitados |
| RN-20 [OBR] | Art. 68 | Reprovação em língua estrangeira optativa não retém na série | 8, 25 | Disciplina com atributo "optativa"; excluída da contagem de componentes para retenção | Caso com optativa reprovada |
| RN-21 [OBR] | Art. 51; Art. 56; Art. 92 §2 | Prevalência do qualitativo; o Conselho de Classe avalia; o coordenador informa o resultado no sistema acadêmico | 8, 22, 25, 26 | Toda saída analítica traz o rótulo "estimativa/apoio, não substitui decisão do Conselho de Classe" | Teste de UI e de exportação: o rótulo está presente |
| RN-22 [OBR] | Art. 72; Art. 69 | Discentes com deficiência podem ser avaliados por portfólio e parecer descritivo | 7, 8, 22 | O sistema **não coleta** dado de deficiência (dado sensível). O professor pode marcar "excluir das estatísticas comparativas" sem informar o motivo | Teste: estudante excluído não entra no ranking/estatística, mas continua no painel individual |
| RN-23 [OBR] | Arts. 78, 80–84 | Abono de faltas, regime domiciliar e guarda religiosa | 23 | Informação ausente no boletim → o sistema mostra "faltas brutas" e avisa que justificativas não são consideradas | Teste de UI |

### 5.2 Pendências de regra (precisam de validação antes de virar regra de negócio)

| Cód. | Pendência | Informação que falta | Quem valida | Proposta provisória (configurável, marcada "não confirmada") |
|---|---|---|---|---|
| PRC-01 | Arredondamento de MB, MA e MF e casas decimais | O Regimento não define. O Anexo 01 sugere arredondamento da AF para cima | CCA/DDE do campus; conferir o comportamento do SUAP | Cálculo com `Decimal`, sem arredondar comparações; exibir 2 casas |
| PRC-02 | MA exatamente 40 | Art. 89 caput exige MA "superior a 40"; §1 trata "inferior a 40"; MA = 40 fica sem cobertura, mas o Anexo 01 lista 40 → 65 | DDE (Art. 104, casos omissos) | Tratar MA = 40 como elegível à AF com mínimo 65 (coerente com o Anexo) |
| PRC-03 | Frequência por componente ou global anual | Arts. 88, 89 e 94 falam em "CH total prevista para o ano letivo"; Art. 54 §4 registra faltas por disciplina; cada PDF contém um diário só | CCA | Indicador por componente; o global só aparece quando todos os diários da turma estiverem importados |
| PRC-04 | Art. 94 §1 remete ao "Art. 59" para faltas justificadas, mas o Art. 59 trata de reposição de avaliações (provável remissão ao Art. 78) | Correção da remissão | DDE/PRE | Seguir o Art. 78 como base |
| PRC-05 | Definição de "rendimento satisfatório" (Art. 64) | Não há número na norma | Coordenação pedagógica | MB ≥ 70 (coerente com o Art. 63) |
| PRC-06 | Faixas de desempenho do TCC (crítica/mediana/boa/excelente) | Só os cortes 40 e 70 têm âncora normativa; o 85/86 não tem | Orientador/coordenação | [0,40) / [40,70) / [70,86) / [86,100], configuráveis, rotuladas [EXP] |
| PRC-07 | Níveis de risco (ID 8) | Nenhuma norma define | Coordenação pedagógica | Ver regra de risco em 8.5 |
| PRC-08 | Layout real do boletim: colunas, faltas, nota de recuperação separada, situação | Amostras reais | Usuário/docentes | Fixtures sintéticos até chegarem amostras |
| PRC-09 | Formato da matrícula (TCC: 12 dígitos) | Confirmação | CCA | Regex configurável; o padrão aceita 12 dígitos |
| PRC-10 | Desvio-padrão populacional ou amostral; método dos quartis | O TCC usa amostral (pandas `.std()`) | Orientador (estatística) | Populacional (a turma é a população), com o rótulo "σ populacional"; quartis pelo método inclusivo (= QUARTIL.INC do Excel) |
| PRC-11 | O que é o "Desenvolvedor" do ID 12 | Não existe como perfil no ID 1 | Coordenação do projeto | Cliente de API com credencial emitida pelo Admin, sem login na interface |
| PRC-12 | Professor pode importar diário de outro professor? Diário com mais de um docente? | — | Coordenação | O diário fica vinculado a quem importou; o coordenador pode reatribuir |
| PRC-13 | Infraestrutura de produção (servidor, domínio, certificado, RPO/RTO, retenção de backup, operador) | — | DTI/TI do campus | Servidor Windows nativo (igual ao dev), mantendo o código portável para Linux |
| PRC-14 | Proteção de dados (LGPD, Lei 13.709/2018, Art. 14: dados de adolescentes) | A norma não está nos documentos fornecidos; é lei federal aplicável | Encarregado de dados do IFPB | Minimização: armazenar só matrícula, nome e notas/faltas; sem CPF, contato ou dado sensível |
| PRC-15 | Catálogo de textos das recomendações pedagógicas (ID 26) | Conteúdo pedagógico | Equipe pedagógica | Rascunho baseado nos mecanismos do Regimento (Núcleos de Aprendizagem Art. 62, recuperação Art. 63, monitoria, Conselho de Classe Art. 64) |
| PRC-16 | Vínculo coordenador ↔ curso(s) | — | Coordenação | Muitos-para-muitos, mantido pelo Admin |
| PRC-17 | Significado do "bimestre informado" no upload, já que o boletim traz os 4 bimestres | — | Usuário/docentes | Bimestre de corte = último bimestre considerado fechado; notas posteriores são ignoradas e reportadas |
| PRC-18 | Integração com a API oficial do SUAP | Fora do escopo da tabela (a entrada é PDF) | Coordenação | Não implementar; registrar como possível evolução futura |

### 5.3 Divergências entre documentos

| Cód. | Divergência | Proposta para validação |
|---|---|---|
| DIV-01 | O TCC usa faixas inconsistentes: §3.2 "0–40/41–69/70–85/86–100"; §3.3 "abaixo de 40, entre 40 e 70"; §4.3 "0–39, 40–69, 70–85, 86–100"; §5.2 "Ruim/Mediana/Boa/Excelente" | Adotar PRC-06 (intervalos semiabertos, robustos a decimais) |
| DIV-02 | TCC §3.4 exclui registros com nota ausente; o Regimento trata ausência como fato relevante (Art. 63 §2) | Nunca descartar em silêncio: o estudante fica com "nota ausente", e as estatísticas informam o n válido e quantos ficaram fora |
| DIV-03 | O TCC usa desvio amostral; a proposta é populacional | PRC-10 |
| DIV-04 | Tabela ID 3: "informa o bimestre"; o boletim do TCC traz os 4 bimestres | PRC-17 |
| DIV-05 | ID 11 lista só "Professor"; ID 2 dá ao Coordenador acesso a todas as turmas do curso | Permitir exportação também ao Coordenador, dentro do seu escopo (validar) |
| DIV-06 | Art. 94 §1 → "Art. 59" (remissão provavelmente incorreta) | PRC-04 |
| DIV-07 | Art. 89 caput × §1 em MA = 40 | PRC-02 |
| DIV-08 | Perfil "Desenvolvedor" (ID 12) inexistente no ID 1 | PRC-11 |
| DIV-09 | O sumário do Regimento cita "Língua Espanhola"; o Cap. X trata de "Línguas Estrangeiras" | Sem impacto; usar o texto do capítulo (atributo "optativa") |

**Separação obrigatória:** as regras [OBR] ficam no módulo `regras`, versionado e com referência ao artigo em cada função. Os critérios [EXP] (faixas, níveis de risco, z-score, ranking) ficam em `analytics`/`estatistica`, parametrizados. Toda regra com PRC aberta tem a flag `confirmada=False`, e a interface mostra o selo "regra pendente de confirmação institucional".

## 6. Arquitetura

### 6.1 Arquitetura atual
Não há sistema no ambiente. A arquitetura do protótipo do TCC (Django MVT síncrono, sem banco, sem autenticação, um PDF por vez, relatório em memória) serve só como referência funcional.

### 6.2 Arquitetura-alvo (monolito modular)

```
 Navegador (HTML + HTMX + Chart.js)      Clientes externos (ID 12)
            │ HTTPS                               │ HTTPS + token
        ┌───▼──────── Proxy reverso (Caddy para Windows ou IIS: TLS, limites de upload) ──┐
        │                                                                                  │
        │  web: Django 5.2 + Waitress (serviço do Windows)                                 │
        │   apps: contas · academico · importacao · notas · regras · estatistica           │
        │         analytics · paineis · relatorios · api (DRF + drf-spectacular)           │
        │         auditoria · ops                                                          │
        └───┬──────────────────────────────────────────────────────────────────────────────┘
            │  ORM (dados + fila)
     PostgreSQL 16 (serviço do Windows) ◄──── worker Django-Q2 `qcluster` (parser, OCR, lote,
            │                                  relatórios, agendamentos: backup) (serviço do Windows)
     pasta de mídia privada (PDFs originais, relatórios gerados; fora do diretório servido)
     tarefa de backup (pg_dump + mídia, compactado/criptografado, retenção) → destino externo (PRC-13)
```
Em desenvolvimento: `runserver` + `manage.py qcluster` em dois terminais. Em produção: Waitress, qcluster e proxy registrados como serviços do Windows (via WinSW/NSSM, a confirmar com a TI). Se a produção for Linux (PRC-13), o mesmo código roda com Gunicorn e systemd.

**Justificativas:**
| Escolha | Motivo |
|---|---|
| Django 5.2 LTS | Suporte longo; auth, sessões, CSRF, admin, ORM e migrações nativos (IDs 1, 2, 13, 15–17); linguagem já conhecida no contexto IFPB/TCC |
| DRF + drf-spectacular | API REST (29), autenticação por token para integração (12) e OpenAPI/Swagger gerado do código (28) |
| PostgreSQL | Integridade relacional, transações, `Decimal` exato, índices para comparações históricas (6, 9, 19) |
| Django-Q2 (broker ORM) | Processamento assíncrono e em lote (18), como o TCC §5.5 propõe (o TCC cita Celery+Redis; troca justificada pela execução nativa no Windows); agendamento para o backup (27); nenhum serviço extra além do PostgreSQL |
| pdfplumber + pypdfium2 | Extração de texto e tabelas com coordenadas; renderização de páginas para OCR sem Poppler |
| pytesseract + Tesseract (idioma `por`) | OCR livre e maduro (5), instalável nativamente |
| Python `decimal` + numpy | Precisão nas regras (Decimal) e desempenho nas estatísticas |
| HTMX + Chart.js (arquivos estáticos locais) | Interatividade sem Node nem build de JavaScript; painéis atualizados por polling ao concluir importações (10) |
| ReportLab + matplotlib | Relatórios PDF sem dependências nativas no Windows (11) |
| openpyxl | Exportação para Excel (30) |
| argon2 + django-axes | Hash de senha forte e bloqueio por força bruta (1) |
| Waitress + serviços do Windows | Execução nativa decidida pelo usuário; o código permanece portável para Linux |

**Camadas dentro de cada app:** `models` (dados) → `services` (casos de uso, transações, checagem de escopo) → `views` HTML e `api` (finas). `regras` e `estatistica` são **funções puras sem Django**, 100% testáveis em unidade.

### 6.3 Modelo de dados proposto (nomes finais a confirmar na E2)
`Usuario` (e-mail institucional único, perfil ∈ {PROFESSOR, COORDENADOR, ADMIN}, ativo) · `Curso` (código SUAP, nome) · `CoordenacaoCurso` (usuário↔curso) · `Turma` (curso, ano letivo, série, identificador) · `Disciplina` (código, ex. "TIN.0054", nome, CH, optativa) · `Diario` (código SUAP, turma, disciplina, professor responsável, ano/período, aulas previstas e ministradas) · `Estudante` (matrícula única, nome) · `MatriculaDiario` (estudante↔diário, situação) · `Importacao` (arquivo, SHA-256, tamanho, bimestre informado, método texto/OCR, versão do parser, status, relatório de validação, usuário, timestamps) · `LoteImportacao` · `RegistroBimestral` (matrícula-diário, bimestre, MB, nota de recuperação, nota registrada, faltas, importação de origem, versão) · `AvaliacaoFinal` (se presente) · `ParametroRegra` (chave, valor, vigência, confirmada) · `SnapshotIndicadores` (escopo, versão das regras, JSON de resultados) · `CatalogoRecomendacao` · `EventoAuditoria` (somente inserção) · `ClienteAPI` (token com hash, escopos).

**Histórico (6/19):** cada importação gera uma nova versão; nada é sobrescrito. A versão "vigente" é a mais recente **confirmada** pelo professor. A reimportação idêntica (mesmo SHA-256) é detectada e não duplica dados.

## 7. Plano de desenvolvimento em etapas

| Etapa planejada | Nome | IDs (principal) | Subetapas de outros IDs | Depende de |
|---|---|---|---|---|
| E0 | Fundação técnica (suporte) | — | — | Aprovação do plano |
| E1 | Infraestrutura e acesso | 1, 2, 15 | 13 (registro de login) | E0 |
| E2 | Modelo de dados e cadastros | 6, 16, 17 | 19 (versionamento), 23 (campos de faltas) | E1 |
| E3 | Importação de boletins | 3, 4, 5, 18 | 13 (eventos de importação) | E2 |
| E4 | Motor de regras e estatísticas | 7, 23, 24, 22 | — | E3 |
| E5 | Learning Analytics | 8, 9, 25, 26 | — | E4 |
| E6 | Dashboards | 10, 20, 21, 19 | 22 (exibição) | E5 |
| E7 | Relatórios e exportações | 11, 30, 31, 32 | 13 (eventos de relatório) | E4, E5 (dados); E6 (gráficos) |
| E8 | API e documentação | 29, 12, 28 | — | E2–E7 (services) |
| E9 | Segurança e auditoria | 13 | revisão de 2, 3, 11, 12 | E1–E8 |
| E10 | Produção | 14, 27 | — | E9 |

**Reorganizações em relação à tabela (justificadas, sem perder os IDs):**
1. **E0 nova:** o ambiente não tem nenhuma ferramenta instalada (seção 3). São só tarefas de suporte, sem funcionalidade de produto.
2. **Dados (orig. 3) antes de Importação (orig. 2):** o parser precisa de um esquema de destino validado, com transação, deduplicação e versionamento. A falta de persistência é a limitação central apontada pelo TCC (§5.4). Importar para um modelo provisório geraria retrabalho.
3. **Auditoria (orig. 9) começa na E1:** login, importação e geração de relatórios devem ser registrados desde que existem (o ID 13 exige isso). A E1 cria o modelo `EventoAuditoria` e o registro de login; a E9 completa consulta, retenção, integridade e revisão. A referência principal continua sendo a E9.
4. **IDs 15–32 com etapa concreta:** 15 → E1 (professor = usuário; o login precisa disso); 16/17 → E2 (entidades base); 18 → E3 (extensão natural do pipeline de upload); 19 → E2 (persistência) + E6 (telas); 23 → E2 (dados) + E4 (indicador e regra de 75%); 22/24 → E4 (cálculos); 25/26 → E5 (dependem do risco); 20/21 → E6; 30/31/32 → E7; 28/29 → E8; 27 → E10. **Prioridade original preservada:** o fato de o ID 15 (Média) ser pré-requisito do ID 1 (Alta) não altera a prioridade, apenas a ordem técnica.

## 8. Detalhamento das tarefas por etapa

Estimativa: P = pequeno, M = médio, G = grande, MG = muito grande. "Arquivos" = módulos prováveis; os nomes exatos serão confirmados na implementação.

### E0 — Fundação técnica (suporte)
- **Objetivo:** ambiente reprodutível e esqueleto do projeto. **Justificativa:** nada está instalado. **Situação atual:** ausente.
- **Tarefas (em ordem):**
  1. (P) **Com autorização do usuário**, instalar via winget: `Python.Python.3.12`, `PostgreSQL.PostgreSQL.16`, `UB-Mannheim.TesseractOCR` (+ `por.traineddata`) e `Git.Git`; desativar o alias "python" da Store; conferir o PATH.
  2. (P) Criar o banco e o usuário `suap_v2` no PostgreSQL local (senha guardada fora do repositório, em `.env`).
  3. (P) `git init` em `PROGRAMA SUAP`, `.gitignore` (inclui `.venv`, `.env` e mídia), `.editorconfig`, README; licença a definir (pendente).
  4. (M) `py -3.12 -m venv .venv`; dependências fixadas (`requirements.txt` + `requirements-dev.txt`, ou pip-tools); esqueleto Django: projeto `config/`, settings separados (base/dev/test/prod) via variáveis de ambiente (django-environ), apps vazias da seção 6.2.
  5. (P) Qualidade: ruff (lint/format), pytest + pytest-django + factory_boy + hypothesis + coverage, pre-commit, bandit, pip-audit; Playwright para Python (`playwright install chromium`).
  6. (P) Scripts PowerShell (`scripts\dev.ps1`, `scripts\test.ps1`, a confirmar) para subir web + qcluster, migrar e testar.
  7. (M) Gerador de **fixtures sintéticos** de boletim (PDF digital via ReportLab + versão rasterizada) imitando o cabeçalho conhecido (Fig. 5 do TCC); dados fictícios.
  8. (P) CI (GitHub Actions com runner Windows ou equivalente, pendente de onde ficará o repositório).
- **Entradas:** nenhuma. **Saídas:** `.\scripts\dev.ps1` sobe a aplicação com a página "ok"; `pytest` roda verde (0 testes de domínio); `tesseract --list-langs` mostra `por`.
- **Riscos:** permissões de administrador para instalar; PATH; antivírus corporativo; versões diferentes entre máquinas de desenvolvedores (mitigado com dependências fixadas e um script de verificação do ambiente). **Testes:** smoke test `/healthz` (db + qcluster + tesseract). **Aceitação:** um checkout limpo, seguindo o README, sobe e passa no lint e nos testes. **Entregáveis:** repositório, scripts, `requirements*`, README de instalação no Windows, fixtures. **Pendente para depois:** CI remoto, se não houver hospedagem definida.

### E1 — Infraestrutura e acesso (IDs 1, 2, 15; parte do 13)
- **Objetivo:** autenticação segura, perfis e escopo de dados. **Situação:** ausente. **Depende de:** E0.
- **Tarefas:**
  1. (M) Modelo `Usuario` customizado (e-mail como login, perfil, ativo); argon2; validação de domínio institucional configurável (`@ifpb.edu.br`/`@academico.ifpb.edu.br`, a confirmar).
  2. (M) Login/logout/troca e redefinição de senha; cookies `Secure`, `HttpOnly`, `SameSite=Lax`; expiração de sessão por inatividade; django-axes (bloqueio após N falhas).
  3. (P) Redirecionamento ao painel do perfil (placeholder até a E6).
  4. (G) **Política de escopo central** (`contas/escopo.py`, a confirmar): `diarios_visiveis(usuario)` → Professor: diários dos quais é responsável; Coordenador: diários de turmas dos seus cursos; Admin: todos. Toda query de domínio passa por ela (views, API, exportações).
  5. (M) Cadastro de professores (ID 15): CRUD pelo Admin; o coordenador consulta os professores do curso; convite por e-mail ou senha inicial com troca obrigatória.
  6. (P) `EventoAuditoria` (somente inserção) + registro de login com sucesso/falha e logout (base do ID 13).
- **Regras:** RN-21 não se aplica; PRC-11/16 influenciam os perfis. **Riscos:** vazamento de escopo é o risco mais grave do sistema; mitigado pela política central + testes de matriz. **Testes:** unitários de escopo; integração login/bloqueio; **matriz de permissões** perfil × recurso × ação (inclui acesso direto por URL/ID de outro professor → 404); CSRF; sessão expirada. **Aceitação:** os 3 perfis entram e caem no painel correto; um professor não acessa diário alheio por nenhuma rota; 5 falhas bloqueiam a conta; o login gera evento de auditoria. **Entregáveis:** telas de login, CRUD de professores, módulo de escopo, testes. **Pendente:** SSO institucional (não pedido; não implementar).

### E2 — Modelo de dados e cadastros (IDs 6, 16, 17; parte do 19 e do 23)
- **Objetivo:** esquema persistente versionado. **Depende de:** E1.
- **Tarefas:**
  1. (G) Modelos da seção 6.3 com restrições: unicidade (matrícula; código do diário + ano; estudante + diário + bimestre + versão), `CHECK` 0 ≤ nota ≤ 100 (RN-01), bimestre 1–4 (RN-19), faltas ≥ 0.
  2. (M) Versionamento: `Importacao` → `RegistroBimestral` com versão e flag "vigente"; serviço de troca de versão vigente em transação.
  3. (M) CRUD de turmas (16) e disciplinas (17) com permissões (Admin e Coordenador no seu curso; professor só leitura) e criação automática a partir do boletim (na E3), com deduplicação por código SUAP.
  4. (P) `ParametroRegra` com seed dos valores do Regimento e das PRC (flag `confirmada`).
  5. (P) Índices para consultas por ano, turma, disciplina e bimestre.
  6. (P) Auditoria de alterações cadastrais (ID 13): quem, quando, antes e depois.
- **Testes:** migrações sobem e descem; restrições violadas geram erro; versionamento (2 importações → 2 versões, 1 vigente); permissões de CRUD. **Aceitação:** é possível consultar notas de qualquer versão histórica; nenhuma operação apaga uma versão anterior. **Entregáveis:** migrações, admin, CRUDs, diagrama ER em `docs/`. **Pendente:** as telas de histórico (E6).

### E3 — Importação de boletins (IDs 3, 4, 5, 18)
- **Objetivo:** PDF do SUAP → dados validados e persistidos. **Depende de:** E2. **Bloqueio para aceite:** PRC-08 (amostras reais).
- **Tarefas:**
  1. (M) Upload (3): formulário com bimestre; limite de tamanho (ex.: 10 MB, a confirmar); verificação de *magic bytes* `%PDF`, PDF não criptografado, número de páginas máximo; SHA-256; armazenamento privado com nome aleatório; registro `Importacao` em status `RECEBIDO`; evento de auditoria.
  2. (M) Pipeline em tarefas Django-Q2: `RECEBIDO → EXTRAINDO → (OCR) → VALIDANDO → AGUARDANDO_CONFIRMACAO → CONCLUIDO | FALHOU`, com tempo limite e novas tentativas; status consultável por polling HTMX.
  3. (G) Detecção do tipo: camada de texto suficiente? Se não houver (ou o texto for ilegível), vai para OCR (5): renderização das páginas com pypdfium2 a ≥ 300 DPI, pré-processamento (escala de cinza, binarização, correção de rotação via OSD do Tesseract), pytesseract `por` com saída TSV (texto + coordenadas + confiança), alimentando o mesmo parser; guarda a confiança média.
  4. (MG) **Parser inteligente (4)**, em camadas:
     (a) Extração do cabeçalho por âncoras textuais ("Curso:", "Diário:", "Ano/Período Letivo:", "Aulas Ministradas:") com regex tolerantes;
     (b) localização da tabela de alunos por cabeçalho de colunas, com **mapeamento por sinônimos** (ex.: "Matrícula/Matr.", "Nome/Aluno", "N1/1º Bim/Nota 1", "Faltas/F", "Situação");
     (c) fallback por coordenadas (clusters de x) quando a detecção de tabela falha;
     (d) normalização: vírgula decimal, "-", vazio, "Cancelado/Transferido" (sinalizar, não descartar em silêncio: DIV-02);
     (e) arquitetura de **perfis de layout** plugáveis (um perfil por variação conhecida) + pontuação de confiança.
  5. (M) Validação: matrícula pelo padrão (PRC-09), notas 0–100, duplicidades no mesmo PDF, nº de alunos > 0, coerência MB × avaliações (RN-02), mínimo de 2 avaliações (RN-18), bimestre informado × colunas presentes (PRC-17), diário já importado (mesmo hash = recusa amigável; hash diferente = nova versão).
  6. (M) Tela de **pré-visualização e confirmação**: o professor revisa o extraído, vê avisos e confirma; só então vira versão vigente.
  7. (G) **Lote (18):** envio de vários PDFs ou ZIP (proteção contra zip-bomb: limite de arquivos e de tamanho descompactado); cada arquivo é processado de forma independente; painel do lote com sucesso/falha por arquivo.
  8. (M) Métricas de qualidade do parser (TCC §5.5): taxa de acerto por campo sobre um conjunto rotulado.
- **Entradas/saídas:** PDF + bimestre → `Importacao` + registros versionados + relatório de validação.
- **Riscos:** layout desconhecido (alto); OCR com erro em dígitos (alto: confundir 7/1 e 0/8 altera notas); PDFs maliciosos. Mitigação: confirmação humana obrigatória; OCR sempre com revisão; parser executado no worker com limites de CPU/tempo.
- **Testes:** PDFs válidos (sintéticos e reais quando houver), inválidos (não PDF renomeado, corrompido, criptografado, vazio, 0 alunos), digitalizados (rasterizados a 150/300 dpi, rotacionados), com layouts diferentes (colunas reordenadas/renomeadas), notas ausentes, matrícula inválida, aluno duplicado, reimportação idêntica, lote com um arquivo ruim. Medir a taxa de extração correta por campo.
- **Aceitação técnica:** 100% dos campos corretos nos fixtures digitais; ≥ 98% nos rasterizados a 300 dpi (meta a validar); nenhum dado gravado sem confirmação; erro sempre explicado ao usuário.
- **Aceitação de negócio:** os mesmos critérios em ≥ 10 boletins reais anonimizados de turmas e disciplinas diferentes (PRC-08).
- **Entregáveis:** pipeline, parser, OCR, tela de confirmação, lote, relatório de acurácia. **Pendente:** novos perfis de layout à medida que surgirem.

### E4 — Motor de regras e estatísticas (IDs 7, 23, 24, 22)
- **Objetivo:** cálculos corretos e explicáveis. **Depende de:** E3.
- **Tarefas:**
  1. (G) `regras/` puro: MB (RN-02), MA (RN-03), recuperação (RN-04/05), AF necessária e MF (RN-10/12, Anexo 01 como tabela de referência + fórmula), situação projetada (RN-08…RN-15, RN-20) e frequência (RN-16/17); cada função cita o artigo; parâmetros vêm de `ParametroRegra` com a flag de confirmação.
  2. (G) `estatistica/` (7): n válido, n ausente, média, mediana, **moda** (multimodal → lista; sem moda → "não há"), variância e desvio (convenção PRC-10, rotulada), mínimo, máximo, amplitude, Q1/Q2/Q3, IQR, coeficiente de variação, "índice de homogeneidade" (CV, conforme a planilha do TCC), distribuição por faixas (PRC-06), % ≥ 70, % < 40, z-score individual.
  3. (M) Frequência (23): % de presença por componente; projeção do limite de 25%; global quando possível (PRC-03).
  4. (M) Índice de recuperação (24) [EXP]: entre os elegíveis (MB < 70), % que atingiram ≥ 70 após a recuperação; ganho médio (registrada − MB); requer nota de recuperação separada no boletim (PRC-08). Definição a validar.
  5. (P) Ranking (22): posição por MB/MA no diário com empates (*dense rank*); exclui marcados RN-22 e sem nota; nunca mostrado ao estudante.
  6. (P) Persistir `SnapshotIndicadores` por escopo + versão das regras; recalcular quando entra uma nova versão vigente.
- **Testes:** unitários com valores calculados à mão; **testes de propriedade** (hypothesis): mínimo ≤ Q1 ≤ mediana ≤ Q3 ≤ máximo, variância ≥ 0, invariância à ordem; conferência contra referência independente (`statistics` da biblioteca padrão e numpy); Anexo 01 inteiro; casos de borda (turma vazia, 1 aluno, todos iguais, notas ausentes, 0 e 100).
- **Aceitação técnica:** 100% dos casos de referência batem com tolerância de 1e-9. **Aceitação de negócio:** separada para regras com PRC aberta.
- **Entregáveis:** bibliotecas puras + documentação das fórmulas em `docs/`. **Pendente:** o painel (E6).

### E5 — Learning Analytics (IDs 8, 9, 25, 26)
- **Depende de:** E4.
- **Tarefas:**
  1. (G) **Risco (8)**, baseado em regras explicáveis [EXP + OBR] (PRC-07), com níveis:
     **Crítico** = MA projetada < 40, ou frequência projetada < 75%, ou rendimento nulo (RN-15/17);
     **Alto** = MA projetada em [40, 70) ou MB < 40 no último bimestre;
     **Atenção** = MB < 70 no último bimestre (RN-04) ou queda ≥ X pontos entre bimestres (X a validar);
     **Adequado** = os demais.
     Cada classificação lista **os motivos** e os artigos.
  2. (G) **Comparações (9):** turmas × turmas (mesma disciplina e ano), disciplinas da mesma turma, bimestres (evolução) e anos; métricas da E4 lado a lado, diferença de médias e boxplots; mostrar n e alertar quando n < 5. Sem testes inferenciais apresentados como conclusão.
  3. (G) **Predição de reprovação (25)**, em duas camadas:
     (a) **projeção determinística** (padrão): média necessária nos bimestres restantes para MA ≥ 70; se insuficiente, AF necessária (Anexo 01); "aprovação matematicamente impossível sem AF/Conselho" quando for o caso;
     (b) **modelo estatístico opcional** (regressão logística), habilitado só com histórico ≥ 2 anos e validação (AUC, calibração, falsos positivos/negativos, como pede o TCC §5.5), atrás de uma feature flag desligada por padrão.
     Rótulo obrigatório "estimativa" (RN-21).
  4. (M) **Recomendações (26):** motor de regras situação → mensagens do `CatalogoRecomendacao` (textos validados pela equipe pedagógica, PRC-15), por exemplo: encaminhar ao Núcleo de Aprendizagem (Art. 62), lembrar a recuperação bimestral (Art. 63), levar ao Conselho de Classe quando > 30% da turma está insatisfatória (Art. 64). Sempre "sugestão".
- **Testes:** casos de cada nível de risco; motivos corretos; projeção bate com o cálculo manual; comparação com n pequeno exibe o aviso; recomendações só disparam nas condições definidas; teste de regressão do modelo opcional com dados sintéticos.
- **Aceitação:** cada saída é reproduzível a partir dos dados e traz explicação; não existe saída sem rótulo de estimativa. **Pendente:** ativar o modelo estatístico (depende de dados históricos reais).

### E6 — Dashboards (IDs 10, 20, 21, 19; exibição do 22)
- **Depende de:** E5.
- **Tarefas:**
  1. (M) Layout base acessível (contraste, teclado, responsivo); painel por perfil: Professor (seus diários, alertas), Coordenador (curso: turmas, alerta do Art. 64, comparações), Admin (uso, importações, falhas, saúde).
  2. (G) Painel da turma/diário (21): cartões de indicadores, histograma, barras ordenadas, pizza/rosca de faixas (os 3 gráficos do TCC), boxplot, evolução bimestral, tabela de risco filtrável e ranking (22).
  3. (G) Painel do aluno (20): notas por bimestre e disciplina, frequência, situação projetada com explicação, posição relativa à turma (percentil, não nome de colegas), recomendações.
  4. (M) Histórico (19): linha do tempo de importações, diferença entre versões, evolução ano a ano.
  5. (M) Filtros (ano, turma, disciplina, bimestre) via HTMX; atualização "em tempo real" = recarga automática ao concluir uma importação (polling ou SSE) e carimbo "atualizado em".
- **Testes:** testes de interface (Playwright) dos fluxos principais; permissões em cada painel; números exibidos = snapshot da E4; acessibilidade básica (axe).
- **Aceitação:** cada perfil vê somente o seu escopo; os valores conferem com os testes da E4; a página da turma carrega em < 2 s com 45 alunos (meta).

### E7 — Relatórios e exportações (IDs 11, 30, 31, 32)
- **Depende de:** E4/E5 (dados) e E6 (gráficos).
- **Tarefas:**
  1. (M) "Conjunto de dados de relatório" único por escopo (cabeçalho do diário e bimestre, estatísticas, listas por faixa/risco, gráficos, rodapé com versão das regras, data, autor e aviso RN-21).
  2. (G) PDF (11): ReportLab (Platypus) + gráficos matplotlib (backend Agg); geração assíncrona em Django-Q2 para relatórios grandes.
  3. (M) Excel (30): abas Resumo / Alunos / Estatísticas / Metadados; tipos numéricos reais.
  4. (P) CSV (31): UTF-8 com BOM, separador `;` (compatível com Excel pt-BR, a confirmar) e cabeçalho estável. (P) JSON (32): esquema versionado e documentado.
  5. (P) Escopo e auditoria em toda exportação; nome de arquivo sem dado pessoal; proteção contra *CSV/Excel injection* (prefixar `=`, `+`, `-`, `@`).
- **Testes:** os 4 formatos contêm os mesmos números (teste de consistência cruzada); abertura dos arquivos por biblioteca leitora; validação do JSON contra JSON Schema; exportação fora do escopo → 403/404; snapshot visual do PDF.
- **Aceitação:** os 4 formatos são gerados para turma e aluno, com números idênticos aos do painel.

### E8 — API e documentação (IDs 29, 12, 28)
- **Depende de:** services das E2–E7.
- **Tarefas:**
  1. (G) Endpoints REST de leitura (29): cursos, turmas, disciplinas, diários, estudantes do escopo, notas, indicadores, riscos e exportações; paginação, filtros e versionamento `/api/v1/`.
  2. (M) Escrita (12): envio de boletim pela API (reusa o pipeline da E3) e cadastros conforme o perfil.
  3. (M) Autenticação: sessão (navegador) + token de cliente (ID 12, PRC-11) com hash, escopos, expiração e revogação pelo Admin; *rate limiting*.
  4. (P) OpenAPI com drf-spectacular + Swagger UI (28) restrito a usuários autenticados em produção.
- **Testes:** contrato (o schema OpenAPI é válido e cobre todos os endpoints); permissões por perfil/token em todos os endpoints; *rate limit*; token revogado → 401.
- **Aceitação:** 100% dos endpoints documentados e cobertos por teste de permissão.

### E9 — Segurança e auditoria (ID 13 + revisão)
- **Tarefas:**
  1. (M) Completar o catálogo de eventos (login, falha de login, importação, confirmação, exportação/relatório, alteração cadastral, alteração de permissão, uso de token, troca de parâmetro de regra).
  2. (M) Tela de auditoria para o Admin (filtros, exportação) e integridade (encadeamento por hash entre eventos, para detectar adulteração).
  3. (P) Política de retenção (PRC-14).
  4. (M) Revisão OWASP Top 10: cabeçalhos (CSP, HSTS, X-Frame-Options), CSRF, XSS (autoescape), SQLi (ORM), IDOR (escopo), upload, segredos em variáveis de ambiente, `DEBUG=False`, dependências (pip-audit), bandit.
  5. (P) Minimização e mascaramento de dados pessoais em logs técnicos.
- **Testes:** cada operação crítica gera exatamente um evento correto; adulteração detectada; varredura de segurança sem achado alto. **Aceitação:** checklist de segurança 100% atendido ou com exceção justificada.

### E10 — Produção (IDs 14, 27)
- **Depende de:** E9 e PRC-13.
- **Tarefas:**
  1. (M) Servidor de produção (Windows, como o desenvolvimento, ou Linux, conforme PRC-13): Waitress + qcluster como serviços (WinSW/NSSM no Windows; systemd + Gunicorn no Linux); proxy Caddy (ou IIS) com HTTPS (Let's Encrypt ou certificado institucional), HSTS e limite de upload; settings `prod` com `DEBUG=False` e segredos fora do repositório.
  2. (M) Backup (27): `pg_dump -Fc` diário + pasta de mídia, compactado e criptografado, agendado pelo Django-Q2 (ou Agendador de Tarefas do Windows); retenção (ex.: 7 diários, 4 semanais, 12 mensais, a validar); cópia fora do servidor; comando `pg_restore` documentado.
  3. (P) **Teste de restauração** em ambiente limpo (obrigatório para aceite).
  4. (M) Monitoramento: `/healthz` e `/readyz` (db, qcluster, tesseract, espaço em disco), logs estruturados, alertas de falha de backup e de fila parada.
  5. (P) Runbook de implantação, atualização, rollback e incidentes; criação do primeiro Admin.
  6. (M) Homologação/piloto com docentes reais (dados reais só após PRC-14).
- **Aceitação:** implantação reproduzível pelo runbook; HTTPS nota A em scanner TLS; restauração bem-sucedida com dados conferidos; alertas disparam em falha simulada.

## 9. Matriz de rastreabilidade (32/32 IDs)

Situação atual de todos os IDs: **Ausente** (não há código). Colunas: ID | Módulo | Funcionalidade | Prior. | Etapa orig. | Etapa plan. | Dependências | Entregável | Critério de aceitação | Testes | Norma | Pendências

| ID | Módulo | Funcionalidade | Pr. | Orig. | Plan. | Dependências | Entregável | Critério de aceitação | Testes | Norma | Pend. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Infraestrutura | Login | Alta | 1 | E1 | E0, 15 | Login por e-mail institucional, sessão segura, painel por perfil | 3 perfis autenticam e caem no painel certo; bloqueio após N falhas; evento auditado | Integração, segurança de sessão, CSRF | — | domínio de e-mail |
| 2 | Infraestrutura | Permissões | Alta | 1 | E1 (revisão E9) | 1 | Política central de escopo | Matriz perfil×recurso 100% verde; IDOR impossível | Matriz de permissões, acesso direto por ID | — | PRC-11, PRC-12, PRC-16 |
| 3 | Importação | Upload PDF | Alta | 2 | E3 | E2 | Upload + bimestre + integridade + pipeline | Arquivo inválido recusado com mensagem; válido segue ao parser; hash registrado | Inválidos, corrompidos, duplicados | RN-01, RN-19 | PRC-17 |
| 4 | Importação | Parser Inteligente | Alta | 2 | E3 | 3 | Parser em camadas com perfis de layout | 100% dos fixtures; ≥ 10 boletins reais corretos | Layouts variados, acurácia por campo | RN-02, RN-05, RN-18 | PRC-08, PRC-09 |
| 5 | Importação | OCR | Média | 2 | E3 | 3, 4 | OCR Tesseract `por` como fallback | Rasterizados a 300 dpi ≥ 98% dos campos (meta) e revisão humana obrigatória | Escaneados, rotação, baixa resolução | RN-01 | PRC-08 |
| 6 | Dados | Banco de Dados | Alta | 3 | E2 | E1 | Esquema PostgreSQL versionado | Nada sobrescrito; consulta por versão e período | Migrações, restrições, versionamento | RN-01, RN-19 | — |
| 7 | Estatísticas | Indicadores | Alta | 4 | E4 | 6 | Biblioteca estatística | Bate com a referência (tol. 1e-9); n válido exibido | Unitários, propriedade, bordas | RN-21 ([EXP]) | PRC-10, PRC-06 |
| 8 | Learning Analytics | Alunos em risco | Alta | 5 | E5 | 7, 23 | Classificação em 4 níveis com motivos | Cada caso-teste no nível correto e com motivo; rótulo de estimativa | Casos por nível | RN-04, RN-08–17, RN-21 | PRC-07 |
| 9 | Learning Analytics | Comparações | Alta | 5 | E5 | 6, 7 | Comparações turma, disciplina, bimestre e ano | Números = E4; aviso para n < 5 | Integração com dados de 2 anos | RN-19 | — |
| 10 | Dashboards | Painéis | Alta | 6 | E6 | 5 | Painéis por perfil, atualização automática | Escopo correto; valores = snapshots; atualiza após importação | Playwright, permissões | RN-07, RN-21 | — |
| 11 | Relatórios | Exportações (PDF…) | Alta | 7 | E7 | 7, 8, 10 | Relatório PDF completo | Contém estatísticas, gráficos e listas; números = painel | Consistência, snapshot | RN-21 | DIV-05 |
| 12 | API | Integração | Média | 8 | E8 | 29 | Tokens de cliente com escopos; escrita via API | Cliente autorizado consulta/envia; revogado → 401 | Contrato, permissões, *rate limit* | — | PRC-11 |
| 13 | Segurança | Logs/Auditoria | Alta | 9 | E9 (início E1) | 1 | Trilha de auditoria íntegra | Todos os eventos do catálogo registrados; adulteração detectada | Evento por operação, integridade | — | PRC-14 |
| 14 | Deploy | Produção | Alta | 10 | E10 | E9, 27 | Ambiente prod com HTTPS e monitoramento | Implantação pelo runbook; TLS A; alertas funcionam | Smoke prod, falha simulada | — | PRC-13 |
| 15 | Funcionalidades | Cadastro de professores | Média | Contínuo | E1 | 1 | CRUD de professores | Admin cria/desativa; desativado não loga; auditado | CRUD + permissões | — | — |
| 16 | Funcionalidades | Cadastro de turmas | Média | Contínuo | E2 | 6 | CRUD + criação automática pelo boletim | Sem duplicata por código; escopo do coordenador | CRUD, deduplicação | RN-19 | PRC-16 |
| 17 | Funcionalidades | Cadastro de disciplinas | Média | Contínuo | E2 | 6 | CRUD + atributo optativa | Sem duplicata; optativa afeta a regra | CRUD, RN-20 | RN-20 | — |
| 18 | Funcionalidades | Processamento em lote | Média | Contínuo | E3 | 3, 4 | Lote assíncrono (múltiplos/ZIP) | Falha de um arquivo não afeta os outros; status por arquivo | Lote misto, zip-bomb | — | — |
| 19 | Funcionalidades | Histórico | Média | Contínuo | E2 + E6 | 6 | Versões + telas de histórico | Toda versão consultável; diferença entre versões | Versionamento, UI | — | — |
| 20 | Funcionalidades | Dashboard do aluno | Média | Contínuo | E6 | 8, 25, 26 | Painel individual (Professor/Coordenador) | Só no escopo; sem nomes de colegas; explicações | Playwright, permissões | RN-21, RN-22 | — |
| 21 | Funcionalidades | Dashboard da turma | Média | Contínuo | E6 | 7, 8 | Painel do diário/turma | Gráficos do TCC + boxplot + risco + alerta Art. 64 | Playwright | RN-07 | PRC-05 |
| 22 | Funcionalidades | Ranking | Média | Contínuo | E4 (+E6) | 7 | Ranking com empates, restrito | Empates corretos; excluídos fora; invisível ao estudante | Unitário, permissões | RN-21, RN-22 | — |
| 23 | Funcionalidades | Frequência | Média | Contínuo | E2 + E4 | 6 | % de presença + projeção do limite de 25% | Cálculo correto; aviso sobre faltas justificadas | Unitário, bordas | RN-08, RN-16, RN-17, RN-23 | PRC-03, PRC-04, PRC-08 |
| 24 | Funcionalidades | Índice de recuperação | Média | Contínuo | E4 | 7, 4 | Índice + ganho médio | Bate com o cálculo manual; só com dado de recuperação | Unitário | RN-04, RN-05 | PRC-08, definição |
| 25 | Funcionalidades | Predição de reprovação | Média | Contínuo | E5 | 8 | Projeção determinística (+ modelo opcional) | Projeção = cálculo manual/Anexo 01; rótulo "estimativa" | Unitário, Anexo 01 | RN-03, RN-09–15 | PRC-01, PRC-02 |
| 26 | Funcionalidades | Recomendações pedagógicas | Média | Contínuo | E5 | 8, 25 | Motor regra → catálogo | Dispara só nas condições; textos validados | Casos por regra | RN-04, RN-07, Art. 62 | PRC-15 |
| 27 | Funcionalidades | Backup | Média | Contínuo | E10 | 6 | Backup criptografado + restore testado | Restauração em ambiente limpo confere dados | Restore test | — | PRC-13 |
| 28 | Funcionalidades | Swagger | Média | Contínuo | E8 | 29 | OpenAPI + Swagger UI | 100% dos endpoints documentados; schema válido | Validação do schema | — | — |
| 29 | Funcionalidades | API REST | Média | Contínuo | E8 | E2–E7 | Endpoints `/api/v1/` | Todos com teste de permissão | Contrato, permissões | — | — |
| 30 | Funcionalidades | Exportar Excel | Média | Contínuo | E7 | 11 | .xlsx | Abre e confere com o painel | Leitura openpyxl | RN-21 | — |
| 31 | Funcionalidades | Exportar CSV | Média | Contínuo | E7 | 11 | .csv | Codificação/separador corretos; anti-injection | Leitura, injection | RN-21 | separador |
| 32 | Funcionalidades | Exportar JSON | Média | Contínuo | E7 | 11 | .json versionado | Valida contra o JSON Schema | Schema | RN-21 | — |

**Conferência:** IDs 1–32 presentes, sem lacunas nem duplicatas → **32/32**. Os IDs 15–32 ("Contínuo") estão todos alocados em E1–E10.

## 10. Plano de testes e critérios de aceitação

| Tipo | Ferramenta | Escopo | Meta |
|---|---|---|---|
| Unitário | pytest, hypothesis | `regras`, `estatistica`, normalizadores do parser | Cobertura ≥ 95% nesses módulos |
| Integração | pytest-django, PostgreSQL local (banco de teste) | services, pipeline Django-Q2 (modo síncrono `sync=True` e real), versionamento | Fluxos E2–E7 |
| Interface | Playwright | login, upload→confirmação, painéis, exportações | Fluxos principais por perfil |
| Permissões | matriz parametrizada | perfil × recurso × ação, inclusive API e exportações | 100% |
| Parser/OCR | corpus rotulado (sintético + real) | acurácia por campo, robustez | Metas da E3 |
| Matemáticos | valores à mão + referência independente + Anexo 01 | todos os indicadores e regras | 100% |
| Regras do Regimento | casos-limite por artigo | RN-01…RN-23 | 100%, separando a validação técnica da institucional |
| Comparações | dados sintéticos de 2 anos e 3 turmas | E5 | Números = E4 |
| Exportações | consistência cruzada dos 4 formatos | E7 | Idênticos |
| API | schema OpenAPI + contrato | E8 | 100% documentado |
| Backup/restore | restauração em ambiente limpo | E10 | Dados idênticos |
| Segurança | bandit, pip-audit, cabeçalhos, OWASP ZAP baseline | E9/E10 | Sem achado alto |

**Casos de borda obrigatórios:** boletim sem alunos; todos sem nota; nota ausente individual; aluno duplicado no PDF; matrícula inválida; aluno "cancelado/transferido"; PDF corrompido, criptografado, vazio ou não PDF; PDF escaneado torto ou de baixa resolução; reimportação idêntica; reimportação com correção; turma com 1 aluno; todos com a mesma nota (desvio 0, moda única, sem variabilidade); MA = 40 (PRC-02); MA = 17 e < 17 (Anexo 01); frequência = 75% exato; CH = 0; > 30% vs = 30% (Art. 64); regra com PRC aberta (deve exibir o selo "pendente").

**Definição de "concluída" para qualquer funcionalidade:** código + testes da matriz verdes + critério de aceitação demonstrado com evidência registrada (saída de teste/relatório anexado à etapa) + documentação atualizada. Para IDs que dependem de PRC: "**tecnicamente concluída**" (comportamento parametrizado e testado) ≠ "**validada institucionalmente**" (PRC respondida e parâmetro marcado como confirmado).

## 11. Riscos, dependências e pendências

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Layout real do boletim diferente do suposto (sem amostras) | Alta | Alto | Perfis de layout plugáveis; aceite da E3 condicionado a amostras reais; confirmação humana |
| Erro de OCR em dígitos altera notas | Média | Alto | OCR só como fallback, com confiança exibida e revisão obrigatória |
| Vazamento de dados de estudantes (menores) | Média | Muito alto | Escopo central, testes de matriz, minimização, auditoria, HTTPS, PRC-14 |
| Estimativas tomadas como decisão oficial | Média | Alto | Rótulos RN-21, explicação dos motivos, nenhuma "situação final" gravada |
| Regras ambíguas (PRC-01…05) | Alta | Médio | Parametrização + selo "pendente"; validação com CCA/DDE |
| Diferenças entre o ambiente nativo Windows de dev e o servidor de produção | Média | Médio | Dependências fixadas; código agnóstico ao servidor WSGI; sem dependências nativas além do PostgreSQL e Tesseract; script de verificação do ambiente |
| Django-Q2 com broker ORM limita a vazão de tarefas | Baixa | Baixo | O volume esperado (boletins de um campus) é baixo; trocar o broker é configuração, não reescrita |
| Infraestrutura de produção indefinida | Média | Médio | PRC-13; aplicação portável Windows/Linux |
| Volume de trabalho para uma equipe pequena | Média | Médio | Etapas incrementais, cada uma entregando valor utilizável |

**Pendências bloqueadoras por etapa:** E0 → autorização para instalar ferramentas. E3 (aceite) → PRC-08 (amostras) e PRC-17. E4/E5 (validação de negócio) → PRC-01…07, 10. E8 → PRC-11. E10 → PRC-13, PRC-14. E5 (recomendações) → PRC-15.

## 12. Estimativas relativas de esforço

| Etapa | Esforço | Risco | Prioridade original dos IDs | Bloqueio | Validação institucional |
|---|---|---|---|---|---|
| E0 | M | Baixo | — (suporte) | Autorização de instalação | Não |
| E1 | M | Médio | Alta (1, 2), Média (15) | — | PRC-11, PRC-16 |
| E2 | G | Baixo | Alta (6), Média (16, 17, 19, 23) | — | — |
| E3 | MG | **Alto** | Alta (3, 4), Média (5, 18) | PRC-08 | PRC-09, PRC-17 |
| E4 | G | Médio | Alta (7), Média (22–24) | — | PRC-01–06, PRC-10 |
| E5 | G | Médio | Alta (8, 9), Média (25, 26) | — | PRC-07, PRC-15 |
| E6 | G | Baixo | Alta (10), Média (19–22) | — | — |
| E7 | M | Baixo | Alta (11), Média (30–32) | — | DIV-05 |
| E8 | M | Baixo | Média (12, 28, 29) | — | PRC-11 |
| E9 | M | Médio | Alta (13) | — | PRC-14 |
| E10 | M | Médio | Alta (14), Média (27) | PRC-13 | PRC-13, PRC-14 |

Não são estimados prazos nem tamanho de equipe, porque faltam informações para isso.

## 13. Critérios gerais de conclusão do projeto
1. Os 32 IDs estão em "tecnicamente concluída", com evidências de teste registradas por etapa.
2. As regras [OBR] foram validadas institucionalmente, ou existe exceção formal registrada para cada PRC não resolvida.
3. O parser foi aceito com boletins reais (PRC-08).
4. Não há achado de segurança alto; matriz de permissões 100% verde.
5. Produção implantada pelo runbook, com HTTPS, backup e restauração testada e monitoramento ativo.
6. A documentação (`docs/`) está atualizada: arquitetura, fórmulas, regras com artigos, API (Swagger), runbook.
7. Piloto com docentes concluído, com feedback registrado.

## 14. Checklist final de cobertura (revisão do §14 do pedido)
- [x] Todos os IDs incluídos (32/32, conferidos na matriz).
- [x] Todos vinculados a uma etapa (IDs 15–32 com etapa concreta e motivo).
- [x] Dependências coerentes (E0→E10; reordenação Dados↔Importação e auditoria antecipada justificadas).
- [x] TCC usado para compreender o sistema original (seção 3), sem reaproveitar código.
- [x] Código inspecionado: não existe; o ambiente foi diagnosticado.
- [x] Regras do Regimento com artigo/parágrafo (RN-01…RN-23).
- [x] Regras não confirmadas sinalizadas (PRC-01…PRC-18) e divergências registradas (DIV-01…DIV-09).
- [x] Todas as funcionalidades têm entregável e critério de aceitação (matriz).
- [x] Testes previstos por tipo e por ID, com casos de borda.
- [x] Funcionalidades complementares com alocação concreta.
- [x] A sequência permite desenvolver, validar e implantar de forma incremental.

## Verificação (como validar este plano e, depois, cada etapa)
- **Do plano:** o usuário revisa as seções 5 (regras/PRC), 7 (ordem) e 9 (matriz) e responde às PRC bloqueadoras.
- **De cada etapa:** `.\.venv\Scripts\python -m pytest` verde (PostgreSQL local) + testes de interface Playwright da etapa + checklist de aceitação da etapa preenchido com evidências em `docs/evidencias/E<n>.md`. Nenhuma etapa é declarada concluída sem esse registro.
