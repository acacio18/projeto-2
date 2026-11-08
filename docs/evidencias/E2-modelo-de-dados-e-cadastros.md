# Evidência — E2: modelo de dados e cadastros (IDs 6, 16 e 17; parte do 19 e do 23) — 08/11/2026

Autorizada pelo usuário em 08/11/2026 ("agora você pode começar o próximo passo, que é a etapa 2").

## O que foi feito

### Parte 1 — modelo, versões, escopo e serviços (commit `16c028d`)
- **Cadastros** (`apps/academico`), identificados pelos códigos do SUAP para não duplicar:
  - `Curso` e `CoordenacaoCurso` (coordenador ↔ curso, muitos-para-muitos, mantido pelo Administrador: PRC-16);
  - `Turma` (curso, ano letivo, série de 1 a 4);
  - `Disciplina` (código único no curso; `optativa` para o Art. 68);
  - `Diario` (código, ano e período únicos; turma opcional; professor responsável);
  - `Estudante` (matrícula no formato configurável, PRC-09);
  - `MatriculaDiario`, com a opção "fora de rankings e comparações" (Art. 72).
- **Versões** (`apps/importacao`): cada boletim importado é uma `Importacao`, numerada por diário (versão 1, 2, 3…), com uma única versão vigente. Os serviços cobrem:
  - `registrar_versao`: recebe os dados no formato do gabarito do boletim, que é o formato que o leitor de PDF da E3 vai produzir;
  - `confirmar_versao`: a confirmação do professor;
  - `definir_versao_vigente`: volta para uma versão anterior;
  - `descartar_versao`: descarta um rascunho;
  - a recusa de um boletim repetido (mesmo SHA-256).
- **Notas** (`apps/notas`): `ResultadoAluno` (situação, faltas, % de frequência, MD, NAF, MFD ou conceito) e `RegistroBimestral` (nota e faltas de cada etapa). As linhas nunca são alteradas; correção chega como nova versão. `-` no boletim vira nulo (ausente, não zero).
- **Imutabilidade em duas camadas:** os modelos recusam a alteração, e os gatilhos do PostgreSQL (`notas/0002`) barram `UPDATE` e `DELETE` numa versão confirmada e nas notas dela. Só o campo `vigente` pode mudar.
- **`ParametroRegra`:** 19 parâmetros iniciais do Regimento e das PRC (`notas/0003`). Cinco são interpretações ou pendências e ficam `confirmada=False`: MA = 40 na AF, rendimento satisfatório, arredondamento, formato da matrícula e faixas de desempenho. Mudar um valor é criar uma nova linha com nova vigência.
- **Escopo central** (`apps/contas/escopo.py`):
  - **diários:** o professor vê os próprios; o coordenador, os do curso que coordena e os próprios; o administrador, todos;
  - **cursos, turmas e disciplinas:** mesma regra;
  - o coordenador vê os professores dos seus cursos (pendência da E1).
- **Serviços dos cadastros** (`apps/academico/servicos.py`):
  - **quem altera:** cursos e coordenadores, só o Administrador; turmas, disciplinas e diários, o Administrador ou o Coordenador do curso;
  - **exclusão:** só do que não está em uso;
  - **auditoria (ID 13):** cada criação, alteração (antes e depois) e exclusão gera um evento.

### Parte 2 — telas (este commit)
- **Navegação:** Painel, Diários, Cadastros e Usuários (só para o administrador). "Alterar senha" virou um botão com ícone no desktop e um item do menu no celular, para o cabeçalho caber em 1024 px.
- **Diários:**
  - lista com busca e filtros (ano; com notas, aguardando confirmação, sem notas, sem turma);
  - detalhe com dados, versões e a tabela de notas no formato do boletim;
  - conferir, confirmar e descartar notas pendentes; ver qualquer versão antiga e torná-la vigente;
  - cadastrar e editar o diário, vinculando turma e professor, e excluir quando não há notas.
- **Cadastros:**
  - página inicial com totais;
  - cursos com coordenação (vincular e remover, só o administrador) e os professores do curso;
  - turmas e disciplinas com busca, filtro por curso e edição só nos cursos que a pessoa gerencia.
- **Painel:** resumo dos diários de cada perfil, com atalhos para os filtros.
- **Demonstração:** `manage.py carregar_exemplo --email <professor>` carrega o boletim de exemplo em duas versões: até o 2º bimestre (alunos "Cursando", frequência sobre 40 aulas) e completa (vigente).
- **Documentação:** diagrama ER e garantias do banco em `docs/design/modelo-de-dados.md`.

## Decisões e desvios
| Assunto | Decisão |
|---|---|
| Turma não vem no boletim | Diário com turma opcional; a coordenação ou a administração vincula. A tela "Editar diário" e o filtro "sem turma" ajudam. |
| Quem cuida das versões (PRC-12) | O professor responsável ou quem gerencia o curso. Um diário novo fica com quem importou, e um diário sem professor passa a ser de quem importar. Professor de outro diário recebe recusa. |
| Persistência antes do leitor de PDF | O serviço que grava versões entrou na E2, no formato do gabarito, porque o versionamento precisava ser testado com dados reais. A E3 acrescenta o envio, a leitura do PDF e a fila. |
| Django admin | Não exposto. Os cadastros passam pelas telas e serviços próprios, que aplicam escopo e auditoria. O plano listava "admin" como entregável; as telas o substituem. |
| Telas de histórico (diferença entre versões, evolução) | Continuam na E6, como previsto. A E2 entrega a consulta de qualquer versão, que é o critério de aceite. |
| Data de vigência dos parâmetros | 2000-01-01: valores do Regimento 2024, valendo também para anos anteriores até se cadastrar outro valor (o boletim de exemplo é de 2023). |

## Defeitos encontrados e corrigidos
1. **Restauração automática dos testes transacionais (`serialized_rollback`).** Depois dos testes com Playwright, a conexão do Django passa a ser outro objeto, e a restauração não acontece. Os parâmetros criados por migração sumiam para os testes seguintes. O teste de migrações foi refeito para não depender do estado inicial: ele desce, sobe e confere. O motivo está documentado no próprio teste.
2. **Dados de demonstração irreais:** a versão "até o 2º bimestre" mostrava "Aprovado" e a frequência final. Ela passou a mostrar "Cursando" e a frequência sobre as aulas dadas até ali.
3. **Layout:** no celular, a coluna do nome ocupava a largura e sumia ao rolar as notas. Agora ela fica fixa à esquerda e mais estreita.

## Critérios de aceitação da E2 (plano, 07-tarefas-por-etapa)
| Critério | Resultado | Prova |
|---|---|---|
| Consultar notas de qualquer versão histórica | OK | `test_versoes_historicas_continuam_consultaveis`, `test_versoes_na_tela_do_diario`, `test_professor_confirma_as_notas_e_volta_para_a_versao_anterior` (navegador) |
| Nenhuma operação apaga uma versão anterior | OK | `test_versao_confirmada_e_imutavel_no_django`, `test_gatilhos_do_banco_protegem_a_versao_confirmada` (6 casos de `UPDATE`/`DELETE` direto no banco), `test_excluir_diario_sem_e_com_notas` |
| 2 importações → 2 versões, 1 vigente | OK | `test_versoes_historicas_continuam_consultaveis` |
| Restrições violadas geram erro | OK | `tests/academico/test_modelos.py` (unicidade, faixas, coerência) e `test_valores_fora_da_regra_sao_recusados_e_nada_fica_gravado` |
| Migrações sobem e descem | OK | `tests/test_migracoes.py` (inclui gatilhos e parâmetros) |
| Permissões de CRUD | OK | `test_matriz_de_permissoes` (perfis × rotas de consulta, alteração e administração) e `tests/academico/test_servicos.py` |
| Professor não acessa diário alheio (pendente da E1) | OK | `test_professor_nao_acessa_diario_alheio_nem_pelo_id`, `test_professor_nao_ve_diario_alheio`, `test_outro_professor_nao_confirma_pela_url` |

## Pre-Delivery Checklist da skill (telas novas)
Capturas em `docs/evidencias/E2-telas/` (11 imagens, de 375 a 1440 px, nos temas claro e escuro), revisadas uma a uma.

| Item | Situação | Como |
|---|---|---|
| Ícones SVG de um conjunto só, sem emoji | OK | 10 ícones Lucide novos, da mesma versão fixa e conferidos; hashes em `docs/design/recursos-de-terceiros.md` |
| `cursor: pointer` e hover sem deslocar o layout | OK | Cartões clicáveis mudam só borda e fundo |
| Contraste nos dois temas | OK | Os tokens não mudaram; `test_contraste.py` continua verde |
| Sem rolagem horizontal em 375, 768, 1024 e 1440 px | OK | `test_telas_da_e2_sem_rolagem_horizontal` (10 páginas × 4 larguras) |
| Tabela larga utilizável no celular | OK | Rola só dentro do quadro (`test_tabela_de_notas_rola_dentro_do_quadro_no_celular`), com a coluna do nome fixa |
| A cor não é o único indicador | OK | Etiquetas com ícone e texto (vigente, aguardando confirmação, sem turma, cancelado) |
| Campos com rótulo e erros ligados | OK | Formulários herdam `FormularioAcessivel`; testes conferem `aria-invalid` |

## Verificações executadas
| Verificação | Resultado |
|---|---|
| `test.ps1` (ruff, formatação, bandit, pytest com cobertura, pip-audit) | 5 etapas OK; **367 passed, 1 skipped** (a rotina de capturas, que só roda com `SUAP_CAPTURAS`); cobertura 100% (1664 linhas) |
| Testes no navegador (Chromium) | 19 passed, inclusive os 6 da E2 (confirmação e troca de versão, 4 larguras sem rolagem, tabela no celular) |
| `makemigrations --check` | Nenhuma mudança pendente |
| Parte 1 no CI | [run 42501292288](https://github.com/acacio18/projeto-2/actions/runs/42501292288): success, 338 testes, cobertura 100% |

## Próximo passo (aguarda autorização)
- **E3: importação de boletins** (IDs 3, 4, 5 e 18): envio do PDF com o bimestre de corte, leitor do boletim (texto e OCR), validação, tela de conferência e confirmação (sobre o serviço de versões da E2) e envio em lote.
