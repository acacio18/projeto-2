# Evidência — E0, tarefas 2 e 3: repositório e banco de dados (25/10/2026)

Autorizadas pelo usuário em 25/10/2026, com identidade de commits "Acácio <lab.nisa.programar@gmail.com>" e autorização para versionar o boletim de exemplo (nomes fictícios).

## Tarefa 3: repositório Git
- `git init -b main` em `PROGRAMA SUAP`; `origin` = `git@github.com:acacio18/projeto-2.git`; os 3 commits existentes foram incorporados (`git reset origin/main`), **sem reescrever o histórico**.
- Configuração local do repositório: `user.name = Acácio`, `user.email = lab.nisa.programar@gmail.com`, `core.autocrlf = true`, `core.quotepath = false`.
- Commit `e6ebaed` (chore): removidos `svgs/icon-cog.svg` e `svgs/icon.trophy.svg` (vazios); `.gitignore` de Laravel substituído por um de Python/Django para Windows; novo `README.md`.
- Commit `a23424d` (docs): `CLAUDE.md`, `docs/planejamento/`, `docs/evidencias/`, `docs/referencias/boletins/exemplo_boletins.pdf`, `.claude/skils/ui-ux-pro-max.zip`.
- `git push origin main`: `5c44c5d..a23424d main -> main` (envio normal, sem force). `git ls-remote origin main` = `a23424d…` = HEAD local.

## Tarefa 2: banco PostgreSQL da aplicação
- Papel `suap_v2` (LOGIN, **CREATEDB**, necessário para o banco de teste do Django) e banco `suap_v2` (dono `suap_v2`, `UTF8`, `TEMPLATE template0`).
- Senha aleatória gravada **somente** em `%USERPROFILE%\.suap_v2\suap_v2_db_password.txt`; o SQL foi executado a partir de um arquivo temporário, apagado em seguida.
- Verificação: `psql -U suap_v2 -d suap_v2` → `suap_v2|suap_v2|UTF8|Portuguese_Brazil.1252`.

## Próximas tarefas da E0 (aguardam autorização)
- Tarefa 4: virtualenv `.venv`, dependências fixadas e esqueleto Django (**primeiro código do programa**).
- Tarefas 5 a 8: ferramentas de qualidade, scripts PowerShell, fixtures de boletim e CI.
