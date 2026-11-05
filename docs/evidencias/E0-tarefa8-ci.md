# Evidência — E0, tarefa 8: integração contínua no GitHub Actions (04/11/2026)

Autorizada pelo usuário em 04/11/2026 ("pode começar o próximo passo").

## O que foi feito
- **`.github/workflows/ci.yml`:** roda em cada push na `main`, em pull requests e sob demanda (`workflow_dispatch`). Usa o runner `windows-2025` e monta o mesmo ambiente nativo do desenvolvimento, com as mesmas versões:

  | Componente | Como é instalado no CI | Versão confirmada na execução |
  |---|---|---|
  | Python | `actions/setup-python` (com cache do pip) + `.venv` + `pip-sync` | 3.12.10 |
  | PostgreSQL | zip oficial da EDB (`16.15-2`), com SHA-256 conferido e pasta em cache; `initdb` em UTF8 com `Portuguese_Brazil.1252` e scram-sha-256, como o banco local; serviço `postgresql-x64-16` na porta 5432; usuário `suap_v2` com CREATEDB | 16.15 |
  | Tesseract | instalador da UB-Mannheim, o mesmo do ambiente local, com SHA-256 igual ao do manifesto oficial do winget; `por.traineddata` de revisão fixa do `tesseract-ocr/tessdata`, idêntico ao arquivo local | 5.4.0.20240606 |
  | Chromium | `playwright install chromium`, com cache | Playwright 1.64.1 |

- **O que o CI executa:** os mesmos scripts do uso local:
  1. `scripts\verificar-ambiente.ps1`;
  2. `manage.py makemigrations --check --dry-run`, que falha se faltar uma migração;
  3. `pre-commit run --all-files`;
  4. `scripts\test.ps1`: ruff, formatação, bandit, pytest com cobertura e testes de navegador, pip-audit.
- **Passo "Resumo":** roda mesmo se algo falhar e publica as versões e o placar do pytest numa anotação e na página da execução. O log do Actions só é legível com login, mesmo em repositório público; a anotação, não.
- **Segurança:**
  - permissões mínimas (`contents: read`), e o `checkout` não guarda credenciais;
  - actions fixadas por SHA de commit: `checkout` v7.0.1, `setup-python` v7.0.0 e `cache` v6.1.0;
  - o `setup-python` v7.1.0 foi evitado por ter só 13 dias;
  - todo download externo é conferido por SHA-256;
  - senhas e `DJANGO_SECRET_KEY` são geradas a cada execução e mascaradas no log, sem segredos no repositório nem nas configurações do GitHub.
- **`.gitattributes`:** PDF, imagens, `.traineddata`, `.xlsx` e `.zip` são marcados como binários, então o Git nunca converte os finais de linha deles. O teste do gabarito confere o SHA-256 do PDF; hoje o Git já detecta o PDF como binário, mas a regra explícita evita depender dessa detecção.
- **Ajuste de apoio:** os dois `# nosec` de `apps/ops/saude.py` passaram para o formato que o bandit entende (`# nosec B404 # justificativa`). No formato antigo, a justificativa era lida como nomes de regras e gerava nove avisos "Test in comment".
- README (selo do CI e seção "Integração contínua") e CLAUDE.md atualizados.

## Decisão: PostgreSQL pelo zip, não pelo Chocolatey
A primeira versão instalava o pacote Chocolatey `postgresql16` 16.15.5 e funcionou, mas esse passo levou **9m17s dos 12m40s** da execução. A imagem do runner traz o PostgreSQL 17, e usá-lo seria rápido, mas o ambiente local e o planejado são o 16.

A solução foi baixar o zip oficial de binários da EDB, extrair só `bin`, `lib` e `share` e guardar a pasta em cache. A EDB não publica hashes desses zips, então o SHA-256 foi calculado no download de 04/11/2026 e fixado no workflow.

O teste local dos binários extraídos foi bloqueado pelo modo automático do Claude Code, por ser código externo. Por isso a validação foi feita na própria máquina descartável do GitHub (execuções 2 e 3).

## Execuções
| # | Commit | O que mudou | Resultado | Duração | PostgreSQL |
|---|---|---|---|---|---|
| 1 | `132b76a` | workflow inicial (Chocolatey) | success | 12m40s | 9m17s |
| 2 | `134013b` | PostgreSQL pelo zip (sem cache) | success | 3m05s | 21s |
| 3 | `c28caa2` | passo "Resumo" (com cache) | success | **2m26s** | 5s + 5s de cache |

Anotação da execução 3 ([run 41953309854](https://github.com/acacio18/projeto-2/actions/runs/41953309854)):
```
Python 3.12.10
postgres (PostgreSQL) 16.15
tesseract v5.4.0.20240606
TOTAL     109      0      4      0   100%
93 passed in 13.44s
```

## O CI falha quando deve
Para não enviar um commit quebrado à `main`, a propagação do código de saída foi verificada localmente. Isso exigiu simular o passo do runner: Windows PowerShell com `$ErrorActionPreference = 'stop'`, a linha de `test.ps1` com `Tee-Object` e o `exit $LASTEXITCODE` que o runner acrescenta.

| Situação | Resultado |
|---|---|
| Com um erro de lint proposital (`apps/ops/_erro_proposital.py`, removido depois) | "Lint (ruff check) FALHA", **código 1** (o passo ficaria vermelho) |
| Sem o erro | "Todas as etapas passaram.", **código 0** |

Os outros passos falham pelo próprio código de saída do comando (`if ($LASTEXITCODE -ne 0) { exit … }` ou `throw` na conferência de hash).

## Fim da Etapa 0
| Tarefa | Evidência |
|---|---|
| 1. Programas instalados | `E0-tarefa1-instalacao.md` |
| 2–3. Repositório e banco | `E0-acesso-repositorio.md`, `E0-tarefas2-3-repositorio-e-banco.md` |
| 4. Esqueleto Django + `/healthz` | `E0-tarefa4-esqueleto-django.md` |
| 5. Ferramentas de qualidade | `E0-tarefa5-qualidade.md` |
| 6. Scripts PowerShell | `E0-tarefa6-scripts.md` |
| 7. Boletins de teste | `E0-tarefa7-fixtures-boletim.md` |
| 8. CI | este arquivo |

O critério de saída da E0 está atendido, com uma parte manual. "Um checkout limpo, seguindo o README, sobe e passa no lint e nos testes" é exatamente o que o CI faz a cada push. A diferença é que ele instala os programas por script; na máquina local, a instalação continua manual, pelo README.

## Próximo passo (aguarda autorização)
- **E1 — Infraestrutura e acesso** (IDs 1, 2 e 15; início do 13): modelo de usuário personalizado e primeira migração, login seguro com bloqueio por tentativas, perfis e política central de escopo, cadastro de professores e registro de login na auditoria. Começa pela descompactação da skill UI/UX Pro Max, pelo `--design-system` e pelas cores oficiais do IFPB.
