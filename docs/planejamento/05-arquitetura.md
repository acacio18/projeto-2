> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 6. Arquitetura

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
