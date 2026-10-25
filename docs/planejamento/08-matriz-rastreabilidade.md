> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 9. Matriz de rastreabilidade (32/32 IDs)

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
