# Evidência — E0, tarefa 4: ambiente virtual, dependências e esqueleto Django (26/10/2026)

Autorizada pelo usuário em 26/10/2026 ("pode começar o próximo passo"). Na mesma mensagem, decidiu: **cores do IFPB** na interface e **descompactar a skill de UI/UX só quando necessário** (registrado em `docs/planejamento/16-diretrizes-ui-ux.md`).

## O que foi feito
- `.venv` com Python 3.12.10; pip 26.2.2; pip-tools 7.6.2.
- `requirements.in` (dependências diretas) → `requirements.txt` (46 pacotes com versão exata, gerado por `pip-compile`), instalado com `pip-sync`. Principais: Django 5.2.18 (LTS), djangorestframework 3.18.3, drf-spectacular 0.30.0, django-environ 0.14.0, waitress 3.0.2, psycopg 3.3.6 (binary), django-q2 1.11.1, argon2-cffi 25.1.0, django-axes 8.3.1, pdfplumber 0.11.10, pypdfium2 5.14.0, pytesseract 0.3.13, pillow 13.0.0, numpy 2.5.4, matplotlib 3.11.2, reportlab 5.1.0, openpyxl 3.1.5. Todas instalaram no Windows sem compilação.
- Projeto `config/`: `settings/base.py` (lê o `.env` via django-environ), `dev.py`, `test.py`, `prod.py`, `urls.py`, `wsgi.py` e `asgi.py`. Idioma `pt-br`, fuso `America/Fortaleza` (IANA, abrange a PB).
- 10 apps Django vazias em `apps/` (contas, academico, importacao, notas, analytics, paineis, relatorios, api, auditoria, ops).
- **Ajuste de estrutura em relação ao plano:** `regras` e `estatistica` ficaram em `dominio/` como pacotes Python puros (sem `AppConfig`), porque o plano exige que sejam funções puras sem Django.
- `GET /healthz` (`apps/ops/views.py`): verifica o banco (`SELECT 1`) e se o Tesseract configurado lista o idioma `por`. Responde 200 se tudo está OK e 503 caso contrário. A verificação da fila (Django-Q2) fica para a E3, quando o worker passar a ser usado.
- `.env.example` (versionado) e `.env` local (ignorado pelo Git, confirmado por `git check-ignore`), com `SECRET_KEY` aleatória e a senha do banco lida de `%USERPROFILE%\.suap_v2\`, sem exibição de segredos.
- **Sem `migrate` de propósito:** o modelo de usuário personalizado (E1) precisa existir antes da primeira migração.

## Verificações executadas
| Verificação | Resultado |
|---|---|
| `python manage.py check` (dev) | `System check identified no issues (0 silenced).` |
| `manage.py check --deploy` (prod) | 1 aviso: `security.W004` (HSTS). Esperado: o HSTS é ativado só na E10, após validar o HTTPS |
| `runserver` + `GET /healthz` | `HTTP 200` `{"status": "ok", "verificacoes": {"banco": true, "tesseract_por": true}}` |
| `GET /nao-existe` | `HTTP 404` |
| `GET /healthz` com `TESSERACT_CMD` inexistente | `HTTP 503` |

Ainda não há testes automatizados: pytest, ruff e os demais vêm na tarefa 5.

## Próximas tarefas da E0 (aguardam autorização)
- Tarefa 5: ferramentas de qualidade (ruff, pytest + pytest-django + factory_boy + hypothesis + coverage, pre-commit, bandit, pip-audit, Playwright) e os primeiros testes do `/healthz`.
- Tarefa 6: scripts PowerShell (`scripts\dev.ps1`, `scripts\test.ps1`).
- Tarefa 7: fixtures de boletim (gabarito JSON do PDF de exemplo + versões rasterizadas para OCR).
- Tarefa 8: CI (GitHub Actions com runner Windows).
