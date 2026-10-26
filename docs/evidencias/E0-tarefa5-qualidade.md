# Evidência — E0, tarefa 5: ferramentas de qualidade e primeiros testes (26/10/2026)

Autorizada pelo usuário em 26/10/2026 ("pode começar o próximo passo").

## O que foi feito
- `requirements-dev.in` → `requirements-dev.txt` (pip-compile, amarrado às versões de execução com `-c requirements.txt`): ruff 0.17.2, pytest 9.1.1, pytest-django 4.14.0, pytest-cov 7.1.0 (coverage 7.17.0), factory-boy 3.3.3, hypothesis 6.170.12, pytest-playwright 0.10.0 (playwright 1.64.1), bandit 1.9.4, pip-audit 2.10.1, pre-commit 4.7.0, pip-tools 7.6.2.
- Navegador Chromium do Playwright instalado (`playwright install chromium`, em `%LOCALAPPDATA%\ms-playwright`).
- `pyproject.toml`: configuração de ruff (linha 110, regras E/W/F/I/B/UP/C4/SIM/DJ/PT), pytest (settings `config.settings.test`, marcador `e2e`), coverage (com branches) e bandit.
- `.pre-commit-config.yaml`: higiene de arquivos (espaços, fim de arquivo, YAML/TOML, conflitos, arquivos > 1 MB, chaves privadas), ruff check/format e bandit, com versões iguais às do `.venv`. Gancho instalado em `.git/hooks/pre-commit`.
- Testes em `tests/`: 8 testes do `/healthz` (`tests/ops/test_healthz.py`) cobrindo 200, idiomas no stderr, 503 sem português, nome de idioma parecido, executável inexistente, timeout, banco indisponível e método POST (405); 1 teste de navegador (`tests/e2e/test_healthz_navegador.py`, Chromium real + `live_server`).
- Formatação do ruff aplicada a 12 arquivos (só uma linha em branco após o docstring).
- Bandit apontou 2 alertas de baixa severidade (B404/B603) sobre o `subprocess` do `/healthz`. São falsos positivos: o comando é fixo, sem shell e sem entrada do usuário. Foram marcados com `# nosec` e justificativa no código.

## Verificações executadas
| Verificação | Resultado |
|---|---|
| `pytest --cov` | **9 passed** em 2,40 s; cobertura **100%** (94 instruções; omitidos settings dev/prod, asgi, wsgi e migrações) |
| `pytest -m "not e2e"` | 8 passed, 1 deselected em 0,89 s |
| `ruff check .` | All checks passed! |
| `ruff format --check .` | 66 files already formatted |
| `bandit -c pyproject.toml -r apps config dominio manage.py` | No issues identified (código 0) |
| `pip-audit -r requirements.txt -r requirements-dev.txt` | No known vulnerabilities found |
| `pre-commit run --all-files` | 10 ganchos: todos Passed |

## Próximas tarefas da E0 (aguardam autorização)
- Tarefa 6: scripts PowerShell (`scripts\dev.ps1`, `scripts\test.ps1`) para subir web + qcluster, migrar e testar.
- Tarefa 7: fixtures de boletim (gabarito JSON do PDF de exemplo + versões rasterizadas para OCR).
- Tarefa 8: CI no GitHub Actions (runner Windows).
