> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 8. Detalhamento das tarefas por etapa

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
