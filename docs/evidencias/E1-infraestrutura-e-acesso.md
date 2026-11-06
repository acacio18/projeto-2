# Evidência — E1: infraestrutura e acesso (IDs 1, 2 e 15; início do 13) — 06/11/2026

Autorizada pelo usuário em 06/11/2026 ("podemos começar o próximo passo, que é a etapa 1"). O design system foi aprovado no mesmo dia, antes de qualquer tela, com as escolhas Open Sans e CSS próprio.

## O que foi feito

### Parte 1 — design system e base sem telas (commit `80fe34c`)
- **Design system** (`docs/design/design-system.md`):
  - gerado pela skill UI/UX Pro Max (`--design-system`, estilo Data-Dense Dashboard), com buscas complementares;
  - cores oficiais do **Manual de Aplicação da Marca IF 2015** (p. 14): verde `#2f9e41` e vermelho `#cd191e`;
  - escalas tonais em OKLCH e contraste WCAG calculado para cada uso.
- **Usuário** (`apps/contas`):
  - login pelo e-mail institucional (domínios configuráveis, padrão `ifpb.edu.br`), sempre em minúsculas;
  - perfis Professor, Coordenador e Administrador, com senhas em argon2;
  - o primeiro administrador sai do `manage.py createsuperuser`.
- **Política central de escopo** (`apps/contas/escopo.py`): só o administrador gerencia usuários. Os demais veem só o próprio cadastro. Registro fora do escopo responde 404.
- **Serviços do cadastro** (`apps/contas/servicos.py`): ninguém se desativa; o sistema nunca fica sem administrador ativo; usuários nunca são apagados.
- **Auditoria** (`apps/auditoria`): `EventoAuditoria` aceita só inclusão, com proteção no modelo e um gatilho no PostgreSQL que barra `UPDATE` e `DELETE`. Registra:
  - login, falha de login, bloqueio e logout;
  - criação, alteração (antes e depois), desativação e reativação de usuários;
  - convites, desbloqueios e senhas.
- **Bloqueio de login** (django-axes): 5 falhas seguidas bloqueiam a conta por 30 min, em qualquer IP e com qualquer grafia do e-mail. O IP vem só do `REMOTE_ADDR`.
- **Sessão:** expira após 30 min sem uso e ao fechar o navegador. Cookies `HttpOnly` e `SameSite=Lax`, e `Secure` em produção.

### Parte 2 — telas (este commit)
- **Telas:**
  - entrar e sair (só POST);
  - alterar senha;
  - esqueci a senha (responde igual para e-mail cadastrado ou não);
  - definir senha pelo link (convite e redefinição; o link vale uma vez e zera o bloqueio);
  - painel por perfil, com resumo de usuários para o administrador;
  - cadastro de usuários: lista com busca, filtros e paginação; novo usuário, que envia o convite; edição; desativação com confirmação; reativação; reenvio do convite; desbloqueio do login;
  - páginas próprias de 403, 403 de CSRF ("formulário expirado"), 404, 429 (conta bloqueada) e 500.
- **Convite:** o administrador cadastra nome, e-mail e perfil, e a pessoa recebe por e-mail um link para criar a própria senha. Ninguém mais conhece a senha. Em desenvolvimento, o e-mail sai no terminal; o SMTP de produção fica para a E10.
- **Interface:**
  - CSS próprio (`static/css/app.css`) com os tokens do design system e os temas claro e escuro (preferência do sistema ou botão);
  - fonte Open Sans hospedada no sistema;
  - ícones Lucide em SVG embutido;
  - JavaScript mínimo, sem código em linha (já pensando na CSP da E9).
  - Origem e SHA-256 de cada recurso de terceiros em `docs/design/recursos-de-terceiros.md`.
- **Acessibilidade dos formulários** (`apps/paineis/formularios.py`): cada campo fica ligado à ajuda e ao erro por `aria-describedby`, com `aria-invalid` quando há erro. O resumo dos erros é anunciado com `role="alert"`.

## Decisões e desvios
| Assunto | Decisão |
|---|---|
| Domínios de e-mail | Padrão só `@ifpb.edu.br`, configurável em `CONTAS_DOMINIOS_EMAIL`. O plano citava também `@academico.ifpb.edu.br`, que é dos estudantes, e estudantes não têm perfil. **Pendente de confirmação institucional.** |
| Bloqueio por conta, não por IP | O axes recomenda incluir o IP (aviso W006). Não foi feito: no campus todos saem pelo mesmo IP público, e 5 erros de pessoas diferentes trancariam todos. O aviso foi silenciado com justificativa no código. Limitação por IP com limite próprio fica para a E9. |
| Prazos (30 min de sessão, 5 falhas, 30 min de bloqueio, link de 72 h, senha de 10 caracteres) | Parâmetros de segurança sem regra institucional. Ficam no `.env`, com padrão documentado no `.env.example`. |
| Coordenador consultar os professores do curso | Fica para a **E2**. O vínculo professor-curso vem dos diários, que ainda não existem (PRC-12 e PRC-16). Na E1 só o administrador vê a lista de usuários. |
| "Professor não acessa diário alheio" (critério da E1 no plano) | Não há diários ainda. A garantia equivalente da E1 está na matriz de rotas × perfis do cadastro e no 404 para registro fora do escopo. A função `diarios_visiveis` entra na E2, no mesmo módulo de escopo, com o teste de diário alheio. |
| Logotipo oficial | Não reproduzido (o manual tem regras próprias de uso). O sistema usa só as cores e o nome "IFPB" em texto. |

## Defeitos encontrados e corrigidos durante a etapa
1. **Bloqueio de login inoperante fora do formulário.** O axes verifica o bloqueio montando as credenciais com a chave `email` (`USERNAME_FIELD`), mas registra as falhas com a chave `username`. A tela de login esconderia o problema, porém o login pela API (E8) nunca bloquearia. Corrigido: a função aceita as duas chaves, `AXES_USERNAME_FORM_FIELD` foi fixado e há um teste de regressão.
2. **Código morto** na regra de "último administrador" da desativação, que nunca podia disparar. Removido.
3. **Layout (achado pela revisão visual e pelos testes no navegador):**
   - rolagem horizontal em 768 px, porque o cabeçalho não cabia; agora a navegação recolhe até 1023 px;
   - botão de menu visível no desktop (especificidade do CSS);
   - cartões desalinhados na grade;
   - tabela cortada no celular; agora as linhas viram cartões com rótulos;
   - vão extra depois dos textos de ajuda.
4. **`ruff format` reformatou os scripts da skill.** A skill foi restaurada do zip e `.claude/` passou a ser ignorada pelo ruff e pelo pre-commit.

## Critérios de aceitação da E1 (plano, 07-tarefas-por-etapa)
| Critério | Resultado | Prova |
|---|---|---|
| Os 3 perfis entram e caem no painel correto | OK | `test_cada_perfil_entra_e_cai_no_seu_painel` (3 casos) e `test_admin_convida_professor_que_cria_a_senha_e_entra` (navegador) |
| Professor não acessa dado alheio por nenhuma rota | OK no que existe na E1 (ver Decisões) | `test_matriz_de_permissoes` (4 perfis × 8 rotas), `test_registro_fora_do_escopo_responde_404_sem_revelar_que_existe`, `test_registro_inexistente_responde_404` |
| 5 falhas bloqueiam a conta | OK | `test_cinco_falhas_bloqueiam_a_conta_mesmo_com_a_senha_certa`, `test_bloqueio_vale_para_a_conta_em_qualquer_ip_e_grafia`, `test_cinco_erros_bloqueiam_e_a_tela_explica` (429) |
| O login gera evento de auditoria | OK | `test_login_e_logout_geram_eventos`, `test_falha_de_login_registra_o_email_digitado_e_nunca_a_senha` |
| CSRF e sessão expirada (testes previstos) | OK | `test_post_sem_token_csrf_e_recusado`, `test_sessao_expira_por_inatividade` |

## Pre-Delivery Checklist da skill UI/UX Pro Max
Capturas em `docs/evidencias/E1-telas/`: 19 imagens, nas larguras 375, 768, 1024 e 1440 e nos temas claro e escuro. Elas foram geradas por `tests/e2e/test_capturas_telas.py` com `SUAP_CAPTURAS` e revisadas uma a uma.

| Item | Situação | Como foi verificado |
|---|---|---|
| Sem emoji como ícone; ícones de um conjunto só (Lucide) | OK | Ícones só pela tag `{% icone %}` (SVG local); revisão das capturas |
| Logotipos corretos | N/A | Nenhum logotipo de marca usado |
| Hover sem deslocar o layout | OK | Hover só muda cor e fundo, sem `transform` nem `scale` no CSS |
| Cores do tema aplicadas pelos tokens | OK (adaptado) | Item escrito para Tailwind; com CSS próprio, todas as cores vêm dos tokens do `:root` |
| `cursor: pointer` nos clicáveis | OK | `.botao` e links; selects e campos mantêm o cursor nativo |
| Feedback de hover e transições de 150 a 300 ms | OK | Transições de 200 ms em cor e fundo |
| Foco visível no teclado | OK | `test_teclado_link_de_pular_e_foco_visivel` (link de pular e anel de foco nos campos) |
| Contraste ≥ 4,5:1 no tema claro e no escuro | OK | `tests/paineis/test_contraste.py`: 52 verificações lidas do próprio CSS (texto ≥ 4,5:1; bordas de campo e foco ≥ 3:1); as duas cópias do tema escuro são iguais |
| Bordas visíveis nos dois temas | OK | Borda de campo `#64748b` (≥ 3:1 nos dois temas) |
| Testar os dois temas | OK | `test_tema_escuro_e_guardado` e capturas nos dois temas |
| Elementos fixos sem cobrir conteúdo | OK | Cabeçalho `sticky`, não sobreposto; capturas |
| Responsivo em 375, 768, 1024 e 1440 px, sem rolagem horizontal | OK | `test_sem_rolagem_horizontal_em_nenhuma_largura` (4 larguras × 6 páginas), `test_menu_no_celular_e_tablet`, `test_botao_de_menu_some_no_desktop` |
| Imagens com texto alternativo | N/A | Não há imagens; os ícones são decorativos (`aria-hidden`) e o sentido está no texto ou no `aria-label` |
| Campos com rótulo | OK | `parciais/campo.html` (`<label for>`), testes com `get_by_label` |
| A cor não é o único indicador | OK | Situações e erros sempre com ícone e texto (etiquetas "Ativo", "Convite pendente", "Desativado") |
| `prefers-reduced-motion` respeitado | OK | Bloco final do CSS desliga transições e animações |

## Verificações executadas
| Verificação | Resultado |
|---|---|
| `test.ps1` (ruff, formatação, bandit, pytest com cobertura, pip-audit) | 5 etapas OK; **269 passed, 1 skipped** (a rotina de capturas, que só roda com `SUAP_CAPTURAS`); cobertura 100% (688 linhas) |
| Testes no navegador (Chromium) | 13 passed (12 da E1 + o `/healthz` da E0); a rotina de capturas é pulada sem `SUAP_CAPTURAS` |
| `makemigrations --check` | Nenhuma mudança pendente |
| Parte 1 no CI | [run 42259854780](https://github.com/acacio18/projeto-2/actions/runs/42259854780): success, 157 testes |

## Próximo passo (aguarda autorização)
- **E2: modelo de dados e cadastros** (IDs 6, 16 e 17; parte do 19 e do 23). Inclui cursos, turmas, disciplinas, diários, estudantes e registros bimestrais versionados; a extensão do escopo para diários (`diarios_visiveis`) com o teste de diário alheio; e a consulta dos professores do curso pelo coordenador.
