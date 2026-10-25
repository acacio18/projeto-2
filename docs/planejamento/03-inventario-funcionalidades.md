> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 4. Inventário completo das funcionalidades (tabela original)

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
