# Evidência — E4: motor de regras e estatísticas (IDs 7, 22, 23 e 24) — 14/11/2026

Autorizada pelo usuário em 14/11/2026 ("pode começar a etapa quatro"), junto com as respostas às pendências de regra. As fórmulas estão em `docs/design/formulas-e-indicadores.md`; as decisões, em `docs/planejamento/14-decisoes-pendencias.md`.

## O que foi feito

### Regras do Regimento (`dominio/regras`, funções puras)
- **`medias`:**
  - média anual (Art. 55 II, só com as 4 etapas);
  - recuperação bimestral e nota registrada (Art. 63);
  - rendimento satisfatório (Art. 64);
  - média final (Art. 91);
  - nota mínima na Avaliação Final, ⌈(500 − 6·MA)/4⌉, que reproduz o Anexo 01 inteiro.
- **`frequencia`:** presença, limite de 25% de faltas (Art. 77), faltas que ainda cabem, alerta precoce e frequência global do ano somando os componentes (PRC-03).
- **`situacao`:**
  - situação projetada de um componente: Em curso, Aprovação projetada, Avaliação Final (com a nota mínima), AF com média abaixo de 40, Conselho de Classe do 4º bimestre, aprovação após a AF, Conselho de Classe Final e Risco de retenção;
  - situação do estudante no ano, com os limites por número de componentes (Arts. 89 §1 e §2, 92, 93 e 94) e os optativos fora da contagem (Art. 68);
  - nunca diz "Reprovado": cada resultado traz o motivo e os artigos.
- **`parametros`:** os limiares chegam prontos de `ParametroRegra`; o domínio não consulta o banco.
- **Interpretações confirmadas** (migração `notas/0004`), conforme decisão do usuário: leitura mais favorável e coerente do Regimento, sem esperar validação institucional. Ficaram confirmadas MA = 40 com AF, rendimento satisfatório ≥ 70, sem arredondamento próprio, matrícula com 12 dígitos e faixas 40/70/86.

### Estatística (`dominio/estatistica`, funções puras)
- **`descritiva` (ID 7):**
  - n, sem nota, média, mediana, moda (multimodal ou "não há"), variância e desvio populacionais (PRC-10);
  - mínima, máxima, amplitude, quartis pelo QUARTIL.INC e IQR;
  - coeficiente de variação com leitura de homogeneidade, % com 70 ou mais e % abaixo de 40;
  - faixas de desempenho (PRC-06), z-score e ranking denso (ID 22).
- **`recuperacao` (ID 24):** o boletim não traz a nota de recuperação separada, então o índice mede a recuperação entre bimestres (abaixo de 70 → 70 ou mais na etapa seguinte) e na Avaliação Final (MF ≥ 50), com o ganho médio.

### Indicadores por versão (`apps/analytics`)
- `indicadores.calcular` monta tudo de uma versão:
  - estatísticas por etapa até o corte e da MD;
  - alerta do Art. 64 por etapa;
  - faixas e situação projetada de cada aluno;
  - posição e z-score;
  - frequência do diário (ID 23) e índice de recuperação.
- **Quem fica de fora:** cancelados ficam fora de tudo. Os marcados "fora de rankings e comparações" (Art. 72) ficam fora das estatísticas e do ranking, mas mantêm situação e frequência.
- `SnapshotIndicadores` (migração `analytics/0001`) guarda o resultado por versão e assinatura. A assinatura junta a versão do cálculo, os limiares, as confirmações e as exclusões. Muda qualquer um, um snapshot novo é calculado, e os antigos ficam como histórico.

### Tela
- **Diário → Indicadores** (para a versão vigente, uma antiga ou a que aguarda confirmação):
  - alerta único para o Conselho de Classe, listando as etapas acima de 30%;
  - cartões de situação projetada, faixas de desempenho e recuperação;
  - tabela de estatísticas por etapa;
  - tabela com a situação de cada estudante: rótulo, motivo e artigos, média de referência, posição e faltas até o limite.
- **Formato e avisos:** números no formato brasileiro (82,75), cada número com a explicação de como foi calculado, e o aviso de que tudo é estimativa.

### Abas no diário (pedido do usuário em 18/11/2026)
- **Duas abas:** o diário passou a ter **Notas do boletim** (padrão: dados do diário, versões e a tabela de notas) e **Análise e indicadores** (tudo o que a E4 mostra), para não acumular tudo numa página longa.
- **Como funcionam:** as abas são links (`?aba=indicadores`), que funcionam sem JavaScript, pelo teclado e com leitor de tela (`nav` com `aria-current`). Cada link pula direto para as abas (`#abas`). Ao trocar de versão, a aba aberta continua a mesma.
- **Desempenho:** os indicadores só são calculados quando a aba deles é aberta.
- **Celular:** as duas abas dividem a largura.
- **Testes:** `test_abas_separam_as_notas_da_analise` e `test_abas_do_diario_no_navegador`. Capturas 27 e 28 em `E4-telas/`.

## Decisões e desvios
| Assunto | Decisão |
|---|---|
| Arredondamento (PRC-01) | O sistema não arredonda: 69,5 continua abaixo de 70. O boletim é oficial; o recálculo meio-para-o-par só confere. |
| MA = 40 (PRC-02) | Tem AF com mínima 65. O usuário falou em "tirar pelo menos 70"; o Regimento (Art. 91) diz média final **50**, e é o que o sistema usa. |
| Índice de recuperação (ID 24) | Redefinido para o que o boletim mostra (entre bimestres e na AF), porque a nota da recuperação bimestral não vem separada. |
| MB por avaliação e mínimo de 2 avaliações (RN-02, RN-18) | Funções prontas (`media_aritmetica`), mas sem uso: o boletim não traz notas por avaliação. |
| Situação do estudante no ano | Função pronta e testada. A tela da E4 mostra a do componente (diário); a do ano depende de todos os diários da turma e entra nos painéis (E6). |
| Frequência para a regra de aprovação | Só a global do ano (PRC-03). O diário mostra a dele como alerta precoce, com "faltas até o limite". |
| Snapshot | Calculado na primeira visita da versão e reaproveitado. Muda a regra, a confirmação ou as exclusões, um snapshot novo é gerado. |
| Gráficos | Ficam para a E6 (dashboards), como no plano. A E4 entrega os números e a tela em tabelas. |

## Defeitos encontrados e corrigidos
1. Mediana guardada como "86.000": o texto agora sai normalizado ("86").
2. Motivos com "68.00": os números do texto saem no formato brasileiro ("68", "82,75").
3. Aluno cancelado aparecia com média de referência (33,33): agora "–".
4. Revisão das capturas:
   - o cabeçalho fixo da tabela de faixas cobria a última linha;
   - quatro alertas separados viraram um só, com a lista das etapas;
   - uma moda com 10 notas empatadas virou "10 notas empatadas";
   - os números quebravam linha no celular;
   - a coluna do indicador não ficava fixa ao rolar;
   - o texto "falta(m) nota(s)" virou português normal.
5. O teste da tabela de notas no celular pegava o último quadro da página, que agora é outro: passou a mirar a tabela de notas e a de estatísticas.

## Critérios de aceitação da E4 (plano, 07-tarefas-por-etapa)
| Critério | Resultado | Prova |
|---|---|---|
| Referências batem com tolerância de 1e-9 | OK | `test_confere_com_statistics_e_numpy` (hypothesis: média, mediana, variância e desvio contra `statistics`; quartis contra `numpy.percentile`), `test_estatisticas_por_etapa_e_da_md` (boletim real contra `statistics`) |
| Valores calculados à mão | OK | `test_resumo_calculado_a_mao`, `test_frequencia_e_limite_de_faltas`, `test_recuperacao_entre_bimestres` |
| Propriedades | OK | `test_propriedades`: mínimo ≤ Q1 ≤ mediana ≤ Q3 ≤ máximo, variância ≥ 0, invariância à ordem, faixas somam n |
| Anexo 01 inteiro | OK | `test_nota_minima_na_af_reproduz_o_anexo_01`: 53 pontos transcritos do PDF; a mínima basta e uma a menos não |
| Bordas | OK | `test_bordas`: turma vazia, 1 aluno, todos iguais, notas ausentes, 0 e 100; `test_nota_minima_fora_da_tabela`; 70 exato, 69,99, 75% exato de frequência, MF 50 exato |
| Regras com artigo | OK | `tests/dominio/test_situacao.py` (14 casos do componente, 14 do estudante, optativa) |
| Domínio sem Django | OK | `test_dominio_nao_importa_django` importa todos os módulos de `dominio/` num Python isolado |
| Ranking com empates e exclusões | OK | `test_z_score_e_ranking_denso`, `test_snapshot_e_reaproveitado_e_refeito_quando_algo_muda` |
| Snapshot por escopo e versão das regras | OK | `test_snapshot_e_reaproveitado_e_refeito_quando_algo_muda`, `test_parametros_do_banco_e_selo_de_pendente` |
| Aceitação de negócio | OK pelas decisões do usuário de 14/11/2026 | `docs/planejamento/14-decisoes-pendencias.md` |

## Pre-Delivery Checklist da skill (tela nova)
Capturas em `docs/evidencias/E4-telas/` (6 imagens: diário completo de Matemática III e diário até o 2º bimestre de Programação para Web com notas faltando; 1440 px nos temas claro e escuro e 375 px), revisadas uma a uma.

| Item | Situação | Como |
|---|---|---|
| Ícones SVG de um conjunto só, sem emoji | OK | Só ícones Lucide que já existiam |
| A cor não é o único indicador | OK | Etiquetas de situação e de frequência com ícone e texto |
| Contraste nos dois temas | OK | Tokens existentes; `test_contraste.py` verde |
| Sem rolagem horizontal da página de 375 a 1440 px | OK | `test_telas_da_e2_sem_rolagem_horizontal` abre o diário com indicadores nas 4 larguras |
| Tabelas largas no celular | OK | Notas e estatísticas rolam dentro do quadro, com a primeira coluna fixa (`test_tabela_de_notas_rola_dentro_do_quadro_no_celular`); a de estudantes vira cartões |
| Tabelas acessíveis | OK | `caption` para leitor de tela, `th scope`, rótulos em cada célula no modo cartão |
| Explicação dos números | OK | Notas de rodapé com o método (desvio populacional, QUARTIL.INC, limite de faltas) e motivo + artigo em cada situação |

## Verificações executadas
| Verificação | Resultado |
|---|---|
| `test.ps1` (ruff, formatação, bandit, pytest com cobertura, pip-audit) | 5 etapas OK; **598 passed, 1 skipped** (a rotina de capturas); cobertura **100%** (3005 linhas, 644 desvios) |
| `makemigrations --check` | Nenhuma mudança pendente |
| CI (commit `3b6fcca`, que inclui a E4) | [run 43662082985](https://github.com/acacio18/projeto-2/actions/runs/43662082985): success, 598 testes, cobertura 100% |

## Próximo passo (aguarda autorização)
- **E5: learning analytics** (IDs 8, 9, 25 e 26):
  - níveis de risco pela qualidade da nota, com os exemplos dados pelo usuário;
  - comparações entre turmas, disciplinas, bimestres e anos;
  - projeção de quanto falta para a média e da Avaliação Final necessária;
  - recomendações pedagógicas com base em conhecimento acadêmico atual.
