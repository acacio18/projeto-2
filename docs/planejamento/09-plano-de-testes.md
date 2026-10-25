> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 10. Plano de testes e critérios de aceitação

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
