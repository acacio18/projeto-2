# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado do projeto

SUAP V2: sistema web para professores e coordenadores do IFPB (cursos técnicos integrados ao ensino médio). Ele importa o PDF "Boletim de Notas do Diário" exportado pelo SUAP, guarda o histórico, calcula estatísticas e aplica as regras do Regimento Didático. Também mostra alunos em risco, comparações, projeções e recomendações, gera relatórios (PDF/Excel/CSV/JSON) e expõe uma API REST.

O projeto está na **Etapa 0 (E0)**. As tarefas 1 a 5 estão concluídas: programas instalados, repositório e banco, esqueleto Django com `/healthz`, e ferramentas de qualidade com os primeiros testes. Ainda não há funcionalidades nem migrações. O planejamento aprovado está em `docs/planejamento/` (comece pelo `README.md`; a matriz dos 32 requisitos fica em `08-matriz-rastreabilidade.md`). As evidências de cada etapa vão em `docs/evidencias/`.

## Regras de trabalho definidas pelo usuário (obrigatórias)

- **Pedir autorização explícita antes de iniciar cada próximo passo** (cada etapa ou tarefa do plano, e sempre antes de escrever código do programa). Seguir a ordem das etapas E0→E10 do plano.
- **Código novo, do zero.** Os repositórios `phmferreira/projectMaths` e `phmferreira/leitordeboletim` e o TCC são do protótipo: servem só para entender os boletins. Nunca copiar nem adaptar o código deles.
- **UI/UX:** toda tela e todo artefato visual seguem a skill **UI/UX Pro Max** (hoje em `.claude/skils/ui-ux-pro-max.zip`; a descompactação em `.claude/skills/ui-ux-pro-max/` aguarda autorização). Começar pelo `--design-system`, salvar o resultado em `docs/design/` e aplicar o Pre-Delivery Checklist da skill no aceite. Detalhes em `docs/planejamento/16-diretrizes-ui-ux.md`.
- Responder em português; salvar os artefatos dentro desta pasta.
- Não inventar regras institucionais. Regras sem base normativa ficam parametrizadas e marcadas "pendente de confirmação" (lista PRC-01…18 em `docs/planejamento/04-regimento-regras-de-negocio.md`; as decisões já tomadas estão em `14-decisoes-pendencias.md`).

## Ambiente (Windows nativo, sem Docker/WSL)

Verificado em 25/10/2026: Git 2.56; Python 3.12.10 (`py -3.12`); PostgreSQL 16.15 como serviço `postgresql-x64-16`, porta 5432; Tesseract 5.4 em `C:\Program Files\Tesseract-OCR\` com os idiomas `eng`, `osd` e `por`. O shell é Windows PowerShell 5.1.

- **Banco da aplicação:** banco e usuário `suap_v2` em `localhost:5432` (o usuário tem CREATEDB para os testes).
- **Senhas:** só em `%USERPROFILE%\.suap_v2\` (`suap_v2_db_password.txt` e `postgres_superuser_password.txt`); nunca copiar para o repositório.
- **Repositório:** `git@github.com:acacio18/projeto-2.git` (público, branch `main`), acessado por deploy key com escrita (`~/.ssh/id_ed25519_suapv2`). Use o `git` normalmente: ele usa o próprio SSH; o OpenSSH do Windows (`System32`) não funciona com o GitHub.
- **Commits:** autor "Acácio <lab.nisa.programar@gmail.com>", configurado no repositório. Mensagens com acento: usar `git commit -F arquivo.txt` (UTF-8), porque o PowerShell 5.1 pode corromper acentos passados como argumento.

## Comandos (PowerShell, na raiz do projeto)

```powershell
.\.venv\Scripts\pip-compile requirements.in      # após editar dependências de execução
.\.venv\Scripts\pip-compile requirements-dev.in  # após editar dependências de desenvolvimento
.\.venv\Scripts\pip-sync requirements.txt requirements-dev.txt   # sincroniza o .venv
.\.venv\Scripts\python -m pytest                 # todos os testes (inclui e2e com Chromium)
.\.venv\Scripts\python -m pytest -m "not e2e"    # rápido, sem navegador
.\.venv\Scripts\python -m pytest tests/ops/test_healthz.py::test_rejeita_metodos_diferentes_de_get   # um teste
.\.venv\Scripts\python -m pytest --cov           # com cobertura
.\.venv\Scripts\ruff check . ; .\.venv\Scripts\ruff format .
.\.venv\Scripts\bandit -c pyproject.toml -r apps config dominio manage.py
.\.venv\Scripts\pip-audit -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\pre-commit run --all-files       # o mesmo que roda em cada commit
.\.venv\Scripts\python manage.py check           # configurações de dev (padrão do manage.py)
$env:DJANGO_SETTINGS_MODULE='config.settings.prod'; .\.venv\Scripts\python manage.py check --deploy
.\.venv\Scripts\python manage.py runserver       # http://127.0.0.1:8000/healthz → 200 se banco e Tesseract/por OK
```

- **Configuração:** fica em `.env` (fora do Git; modelo em `.env.example`). `manage.py` usa `config.settings.dev`; `wsgi.py` e `asgi.py` usam `config.settings.prod`; o pytest usa `config.settings.test` (definido no `pyproject.toml`).
- **Testes:** ficam em `tests/`, espelhando as apps (`tests/ops/…`). Os de navegador ficam em `tests/e2e/`, com o marcador `e2e`; o `conftest.py` dessa pasta liga `DJANGO_ALLOW_ASYNC_UNSAFE` por causa do Playwright síncrono. O banco de teste (`test_suap_v2`) é criado pelo usuário `suap_v2`, que tem CREATEDB.
- **Pre-commit:** roda ruff e bandit em cada commit. Um `# nosec` exige justificativa no próprio código.
- **Terminais antigos:** se não acharem `python`, `py` ou `git` (abertos antes da instalação), use os caminhos do `.venv` ou recarregue o PATH.
- **Sem `migrate` até a E1:** o modelo de usuário personalizado precisa existir antes da primeira migração.
- **Ainda não existem:** os scripts em `scripts\` (tarefa 6 da E0) e o CI (tarefa 8).

## Arquitetura-alvo (ver `docs/planejamento/05-arquitetura.md`)

Monolito Django 5.2 modular + DRF + PostgreSQL. Templates Django + HTMX + Chart.js, com Tailwind via CLI standalone (sem Node). Escolhas por rodar nativo no Windows: **Django-Q2** com broker ORM no lugar de Celery/Redis, **Waitress** no lugar de Gunicorn, **ReportLab** no lugar de WeasyPrint e **pypdfium2 + pytesseract** no lugar de OCRmyPDF/Poppler.

Princípios que atravessam vários módulos:
- **Estrutura:** apps Django em `apps/<nome>` (contas, academico, importacao, notas, analytics, paineis, relatorios, api, auditoria, ops). `dominio/regras` (Regimento) e `dominio/estatistica` são **funções puras, sem Django**, com `Decimal`, e não podem importar `django`. Cada regra cita o artigo do Regimento e lê os limiares de `ParametroRegra`, que tem a flag `confirmada`.
- **Escopo de dados central:** toda consulta de domínio (views, API, exportações) passa por uma única política de escopo. Professor vê só os próprios diários; Coordenador, os diários do curso; Admin, tudo. Não existe perfil "Aluno": o "dashboard do aluno" é um painel sobre o aluno, visto por professor e coordenador.
- **Importação versionada:** cada PDF gera uma nova versão (nada é sobrescrito); a versão vigente só muda após confirmação do professor; hash SHA-256 evita duplicatas. O pipeline roda em tarefas Django-Q2: texto via pdfplumber, OCR como fallback.
- Toda saída analítica (risco, ranking, predição, recomendação) é **estimativa** com motivo explicado. O sistema nunca grava resultado acadêmico oficial, porque a decisão é do Conselho de Classe.
- Auditoria só de inserção (`EventoAuditoria`) desde a E1.

## Formato do boletim SUAP (fixture de referência: `C:\Users\Pichau\Downloads\exemplo_boletins.pdf`)

PDF com camada de texto. Cabeçalho por rótulos: `Curso:`, `Diário:` (`70764 - TIN.0054 - Nome - Médio [67 h/80 Aulas]`), `Ano/Período Letivo:`, `Aulas Ministradas:`. Colunas: `# | Matrícula (12 dígitos) | Nome | T. Faltas | % Freq. | Situação | E1..E4 (N, F) | MD | NAF (N, F) | MFD/Conceito`. A tabela continua na página 2 sem repetir o cabeçalho. `-` significa ausente, não zero. Alunos `Cancelado` ficam fora das estatísticas. Os 4 bimestres vêm no mesmo PDF; o bimestre informado no upload é o "corte". **Não há** nota de recuperação bimestral separada nem notas por avaliação. Análise completa em `docs/planejamento/15-analise-boletim-exemplo.md`.

## Regras do Regimento mais usadas (Regimento Didático Integrado 2024)

- Notas de 0 a 100. MB = média aritmética das avaliações; MA = (MB1+MB2+MB3+MB4)/4 (Art. 55).
- Recuperação bimestral se MB < 70; prevalece a maior nota (Art. 63).
- Aprovado: MA ≥ 70 e frequência ≥ 75% da carga horária **total do ano** (Art. 88). Avaliação Final se 40 ≤ MA < 70 (MA = 40 incluída: PRC-02). MA < 40 em até 3 componentes também tem AF, com a nota mínima do Anexo 01.
- MF = (6·MA + 4·AF)/10, aprovado com MF ≥ 50 (Art. 91).
- Alerta de Conselho de Classe quando mais de 30% da turma tem nota da etapa < 70 (Art. 64, interpretação PRC-05).
- Arredondamento: os valores do boletim são oficiais. O recálculo só confere, usando meio para o par (*half-even*), comportamento observado no SUAP (PRC-01).
