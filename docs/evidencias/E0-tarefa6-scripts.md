# Evidência — E0, tarefa 6: scripts PowerShell de uso diário (04/11/2026)

Autorizada pelo usuário em 04/11/2026 ("podemos começar o próximo passo").

## O que foi feito
- `scripts\verificar-ambiente.ps1`: confere o `.venv` com Python 3.12, as dependências instaladas iguais a `requirements*.txt` (`pip-sync --dry-run`), o `.env` preenchido (sem os valores de exemplo), o serviço do PostgreSQL em execução, o Chromium do Playwright e, via `manage.py verificar_saude`, o banco e o Tesseract com português. Cada falha vem com a dica de correção; termina com código 1 se houver falha. O parâmetro `-ServicoPostgres` permite outro nome de serviço.
- `scripts\dev.ps1`: roda a verificação do ambiente (dispensável com `-SemVerificacao`), inicia o `qcluster` **quando o Django-Q2 estiver em `INSTALLED_APPS`** (previsto para a E3; até lá avisa e sobe só o web) e sobe o `runserver` em `127.0.0.1` (`-Porta`, padrão 8000). Ao encerrar, finaliza a árvore de processos da fila (`taskkill /T`).
- `scripts\test.ps1`: lint (ruff check), formatação (ruff format --check), bandit, pytest com cobertura e pip-audit. Todas as etapas rodam mesmo com falha, e no fim aparece um resumo; código 1 se algo falhou. `-Rapido` pula os testes de navegador e o pip-audit.
- Scripts gravados em **UTF-8 com BOM**, porque o Windows PowerShell 5.1 lê arquivos sem BOM como ANSI e corromperia os acentos.
- **Refatoração de apoio:** as verificações do `/healthz` foram movidas para `apps/ops/saude.py` (`banco_responde`, `tesseract_tem_portugues`, `verificar`), reutilizadas pela view e pelo novo comando `manage.py verificar_saude` (`apps/ops/management/commands/`). Os testes do `/healthz` passaram a simular o módulo `saude`; 2 testes novos cobrem o comando.
- **Política de execução:** o Windows bloqueia `.ps1` por padrão (LocalMachine/CurrentUser = Undefined → Restricted). Os scripts são chamados com `powershell -ExecutionPolicy Bypass -File …`, que vale só para aquele comando, sem alterar a configuração da máquina.

## Verificações executadas
| Verificação | Resultado |
|---|---|
| `verificar-ambiente.ps1` | 8 linhas OK, "Ambiente pronto.", código 0 |
| `verificar-ambiente.ps1 -ServicoPostgres servico-que-nao-existe` | `FALHA Serviço do PostgreSQL…` com dica, "Ambiente com 1 falha(s).", código 1 |
| `test.ps1` | 5 etapas OK (ruff check, ruff format com 72 arquivos, bandit, pytest **11 passed** com cobertura 100%, pip-audit sem vulnerabilidades), código 0 |
| `test.ps1 -Rapido` com erro de lint proposital (arquivo temporário, removido depois) | Lint FALHA (F401), demais OK, "Há etapas com falha.", código 1 |
| `dev.ps1 -Porta 8790` | ambiente OK → aviso "fila ainda não configurada" → `GET /healthz` HTTP 200; porta liberada ao encerrar |
| `manage.py verificar_saude` | 2 linhas OK, código 0 |
| `pre-commit run --all-files` | 10 ganchos Passed |

## Próximas tarefas da E0 (aguardam autorização)
- Tarefa 7: fixtures de boletim (gabarito JSON do PDF de exemplo + versões rasterizadas para OCR).
- Tarefa 8: CI no GitHub Actions (runner Windows).
