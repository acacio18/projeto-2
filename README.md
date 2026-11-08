# SUAP V2

[![CI](https://github.com/acacio18/projeto-2/actions/workflows/ci.yml/badge.svg)](https://github.com/acacio18/projeto-2/actions/workflows/ci.yml)

Sistema web de apoio a professores e coordenadores do **IFPB** (cursos técnicos integrados ao ensino médio). Ele lê o PDF "Boletim de Notas do Diário" exportado pelo SUAP e transforma as notas em estatísticas, painéis, alertas de alunos em risco, comparações entre turmas e bimestres, projeções e relatórios. Tudo segue o Regimento Didático dos Cursos Técnicos Integrados do IFPB (2024).

É uma reimplementação completa, escrita do zero, da proposta do TCC *"Automação do tratamento estatístico das notas dos alunos do IFPB pelo SUAP para docentes"* (IFPB Campus Itaporanga, 2025).

> **Aviso:** os indicadores, riscos e projeções do sistema são **apoio pedagógico e estimativas**. Eles não substituem o registro oficial no SUAP nem as decisões do Conselho de Classe.

## Situação

Em desenvolvimento. Etapas concluídas:
- **E0, fundação técnica:** ambiente, testes, scripts, boletins de teste e integração contínua.
- **E1, acesso:** login pelo e-mail institucional, perfis Professor, Coordenador e Administrador, cadastro de usuários com convite por e-mail, bloqueio após 5 senhas erradas, auditoria e telas com tema claro e escuro.
- **E2, dados e cadastros:** cursos com coordenadores, turmas, disciplinas e diários; notas guardadas em versões (nada é sobrescrito; uma versão vigente por diário); cada um vê só o seu escopo.

Próxima: E3 (importação dos boletins em PDF).

## Documentação

- [Planejamento completo](docs/planejamento/README.md): requisitos (32 funcionalidades), regras do Regimento, arquitetura, etapas E0–E10, matriz de rastreabilidade e plano de testes.
- [Decisões sobre regras pendentes](docs/planejamento/14-decisoes-pendencias.md)
- [Análise do boletim SUAP de exemplo](docs/planejamento/15-analise-boletim-exemplo.md); o PDF (nomes fictícios) está em [docs/referencias/boletins/](docs/referencias/boletins/)
- [Diretrizes de UI/UX](docs/planejamento/16-diretrizes-ui-ux.md) e [design system](docs/design/design-system.md) (cores oficiais do IF, tipografia, componentes)
- [Modelo de dados](docs/design/modelo-de-dados.md) (diagrama e garantias do banco)
- [Evidências por etapa](docs/evidencias/)

## Stack prevista

Python 3.12 · Django 5.2 · Django REST Framework · PostgreSQL 16 · Django-Q2 · Tesseract OCR (português) · HTMX · Chart.js · Tailwind CSS. Execução nativa no Windows, sem Docker.

## Pré-requisitos do ambiente (Windows)

- Python 3.12, PostgreSQL 16, Tesseract OCR 5 com o idioma `por` e Git.
- Ambiente virtual e dependências: `py -3.12 -m venv .venv` e `.venv\Scripts\pip install pip-tools`, depois `.venv\Scripts\pip-sync requirements.txt requirements-dev.txt` e `.venv\Scripts\playwright install chromium`.
- Configuração: copie `.env.example` para `.env` e preencha.

## Como rodar (PowerShell, na raiz do projeto)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verificar-ambiente.ps1   # confere se está tudo pronto
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1                  # sobe em http://127.0.0.1:8000 (saúde: /healthz)
powershell -ExecutionPolicy Bypass -File scripts\test.ps1                 # lint, segurança, testes e auditoria de dependências
```

### Primeiro acesso

```powershell
.\.venv\Scripts\python manage.py migrate            # cria as tabelas (rode de novo depois de cada atualização)
.\.venv\Scripts\python manage.py createsuperuser    # primeiro administrador (e-mail @ifpb.edu.br)
```

Para ver diários com notas antes da importação de PDF (E3), carregue o boletim de exemplo: `.\.venv\Scripts\python manage.py carregar_exemplo --email <e-mail de um professor>`.

Depois, entre em http://127.0.0.1:8000 e cadastre os professores e coordenadores em **Usuários**. Cada um recebe um convite por e-mail para criar a própria senha. Em desenvolvimento, o e-mail aparece no terminal do `dev.ps1`.

## Integração contínua

A cada envio para a `main` e em cada pull request, o GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) monta numa máquina Windows o mesmo ambiente acima, com as mesmas versões. Depois roda `verificar-ambiente.ps1`, a checagem de migrações pendentes, o pre-commit e o `test.ps1`. O selo no topo desta página mostra o resultado da última execução.
