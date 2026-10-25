> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 7. Plano de desenvolvimento em etapas

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
