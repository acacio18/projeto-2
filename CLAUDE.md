# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado do projeto

SUAP V2: sistema web para professores e coordenadores do IFPB (cursos técnicos integrados ao ensino médio). Ele importa o PDF "Boletim de Notas do Diário" exportado pelo SUAP, guarda o histórico, calcula estatísticas e aplica as regras do Regimento Didático. Também mostra alunos em risco, comparações, projeções e recomendações, gera relatórios (PDF/Excel/CSV/JSON) e expõe uma API REST.

A **Etapa 0 (E0) está concluída** (tarefas 1 a 8): programas instalados, repositório e banco, esqueleto Django com `/healthz`, ferramentas de qualidade com os primeiros testes, scripts PowerShell, fixtures de boletim e CI no GitHub Actions. A **E1 está concluída**: design system aprovado, login, perfis, política de escopo, cadastro de usuários com convite por e-mail, auditoria e telas. A evidência está em `docs/evidencias/E1-infraestrutura-e-acesso.md`. A próxima é a **E2** (modelo de dados e cadastros), que depende de autorização. O planejamento aprovado está em `docs/planejamento/` (comece pelo `README.md`; a matriz dos 32 requisitos fica em `08-matriz-rastreabilidade.md`). As evidências de cada etapa vão em `docs/evidencias/`.

## Regras de trabalho definidas pelo usuário (obrigatórias)

- **Pedir autorização explícita antes de iniciar cada próximo passo** (cada etapa ou tarefa do plano, e sempre antes de escrever código do programa). Seguir a ordem das etapas E0→E10 do plano.
- **Código novo, do zero.** Os repositórios `phmferreira/projectMaths` e `phmferreira/leitordeboletim` e o TCC são do protótipo: servem só para entender os boletins. Nunca copiar nem adaptar o código deles.
- **UI/UX:** toda tela e todo artefato visual seguem a skill **UI/UX Pro Max**, descompactada em `.claude/skills/ui-ux-pro-max/`. Ela fica idêntica ao zip original em `.claude/skils/`, e por isso o ruff e o pre-commit a ignoram. Os scripts rodam com `python -E -s` (o `-I` impede o script de importar o próprio `core.py`). O design system está em `docs/design/design-system.md`, com as cores oficiais do IF e os contrastes. Aplique o Pre-Delivery Checklist da skill no aceite. Detalhes em `docs/planejamento/16-diretrizes-ui-ux.md`.
- Responder em português; salvar os artefatos dentro desta pasta.
- Não inventar regras institucionais. Regras sem base normativa ficam parametrizadas e marcadas "pendente de confirmação" (lista PRC-01…18 em `docs/planejamento/04-regimento-regras-de-negocio.md`; as decisões já tomadas estão em `14-decisoes-pendencias.md`).

## Ambiente (Windows nativo, sem Docker/WSL)

Verificado em 25/10/2026: Git 2.56; Python 3.12.10 (`py -3.12`); PostgreSQL 16.15 como serviço `postgresql-x64-16`, porta 5432; Tesseract 5.4 em `C:\Program Files\Tesseract-OCR\` com os idiomas `eng`, `osd` e `por`. O shell é Windows PowerShell 5.1.

- **Banco da aplicação:** banco e usuário `suap_v2` em `localhost:5432` (o usuário tem CREATEDB para os testes).
- **Senhas:** só em `%USERPROFILE%\.suap_v2\` (`suap_v2_db_password.txt` e `postgres_superuser_password.txt`); nunca copiar para o repositório.
- **Repositório:** `git@github.com:acacio18/projeto-2.git` (público, branch `main`), acessado por deploy key com escrita (`~/.ssh/id_ed25519_suapv2`). Use o `git` normalmente: ele usa o próprio SSH; o OpenSSH do Windows (`System32`) não funciona com o GitHub.
- **Commits:** autor "Acácio <lab.nisa.programar@gmail.com>", configurado no repositório. Mensagens com acento: usar `git commit -F arquivo.txt` (UTF-8), porque o PowerShell 5.1 pode corromper acentos passados como argumento.

## Comandos (PowerShell, na raiz do projeto)

Scripts de uso diário. O Windows bloqueia `.ps1` por padrão, então chame-os com `-ExecutionPolicy Bypass`, que vale só para aquele comando:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verificar-ambiente.ps1   # .venv, dependências, .env, PostgreSQL, Chromium, banco e Tesseract
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1                  # verifica o ambiente e sobe o servidor (e a fila, quando houver)
powershell -ExecutionPolicy Bypass -File scripts\test.ps1                 # ruff, bandit, pytest --cov, pip-audit (-Rapido: sem e2e e sem pip-audit)
```

Os `.ps1` precisam ficar em **UTF-8 com BOM**: o PowerShell 5.1 lê arquivos sem BOM como ANSI e corrompe os acentos.

Comandos avulsos:

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
.\.venv\Scripts\python manage.py verificar_saude # mesmas verificações do /healthz no terminal (código 1 se falhar)
```

- **Saúde:** as verificações ficam em `apps/ops/saude.py`, e a view `/healthz`, o comando `verificar_saude` e os scripts usam esse módulo. Uma verificação nova entra em `saude.verificar()`.

- **Configuração:** fica em `.env` (fora do Git; modelo em `.env.example`). `manage.py` usa `config.settings.dev`; `wsgi.py` e `asgi.py` usam `config.settings.prod`; o pytest usa `config.settings.test` (definido no `pyproject.toml`).
- **Testes:** ficam em `tests/`, espelhando as apps (`tests/ops/…`). Os de navegador ficam em `tests/e2e/`, com o marcador `e2e`; o `conftest.py` dessa pasta liga `DJANGO_ALLOW_ASYNC_UNSAFE` por causa do Playwright síncrono. O banco de teste (`test_suap_v2`) é criado pelo usuário `suap_v2`, que tem CREATEDB.
- **Pre-commit:** roda ruff e bandit em cada commit. Um `# nosec` exige justificativa no próprio código.
- **Terminais antigos:** se não acharem `python`, `py` ou `git` (abertos antes da instalação), use os caminhos do `.venv` ou recarregue o PATH.
- **Banco:** depois de puxar mudanças, rode `.\.venv\Scripts\python manage.py migrate`. O usuário é `contas.Usuario`, com login pelo e-mail institucional e perfil PROFESSOR, COORDENADOR ou ADMIN. O primeiro administrador é criado com `manage.py createsuperuser`. A tabela de auditoria tem um gatilho no PostgreSQL que barra `UPDATE` e `DELETE` (migração `auditoria/0002`).
- **Contas (E1):**
  - regras de acesso só em `apps/contas/escopo.py`;
  - casos de uso do cadastro em `apps/contas/servicos.py`, porque as views só chamam os serviços;
  - auditoria pelo `apps/auditoria/registro.registrar()`; login, logout, falha e bloqueio são gravados por sinais em `apps/auditoria/sinais.py`;
  - bloqueio por tentativas pelo django-axes, por conta e não por IP (justificativa em `config/settings/base.py`);
  - em testes, use `client.force_login`, porque `client.login` não passa a requisição que o axes exige.
- **Telas:**
  - templates em `templates/` (bases `base.html`, para quem está logado, e `base_acesso.html`, para login e senhas; parciais em `templates/parciais/`, como `campo.html` para campos acessíveis);
  - CSS próprio em `static/css/app.css`, com tokens do design system e temas claro e escuro; JS em `static/js/`, sem código em linha;
  - ícones com `{% load interface %}{% icone "nome" %}` (SVGs Lucide em `apps/paineis/icones/`);
  - formulários herdam `apps.paineis.formularios.FormularioAcessivel`;
  - não use `style=` nos templates: crie uma classe no CSS (CSP da E9).
- **Testes de interface:**
  - `tests/paineis/test_contraste.py` lê os tokens do CSS e exige contraste WCAG nos dois temas;
  - `tests/e2e/test_acesso_navegador.py` cobre o fluxo do convite, as larguras de 375 a 1440 px, o menu, o tema, a senha e o teclado;
  - capturas para revisão visual: `$env:SUAP_CAPTURAS='pasta'; .\.venv\Scripts\python -m pytest tests/e2e/test_capturas_telas.py`.
- **Fábricas de teste:** `tests/apoio/fabricas.py` (`ProfessorFactory`, `CoordenadorFactory`, `AdminFactory`; senha padrão `SENHA_PADRAO`).
- **Boletins de teste:** o gabarito JSON do boletim de exemplo fica em `tests/fixtures/boletins/` (detalhes no `README.md` dessa pasta). As fixtures `boletim_exemplo`, `gabarito_exemplo` e `boletim_digitalizado("300dpi" | "150dpi" | "300dpi_inclinado" | "300dpi_girado90")` estão em `tests/conftest.py`. As versões digitalizadas (só imagem, para OCR) são geradas na hora por `tests/apoio/digitalizacao.py` e não são versionadas. O código de apoio aos testes fica em `tests/apoio/`.
- **CI:** `.github/workflows/ci.yml` roda em cada push na `main` e em pull requests. Ele usa o runner `windows-2025`, instala as mesmas versões do ambiente local e executa `verificar-ambiente.ps1`, `makemigrations --check`, o pre-commit e o `test.ps1`. As versões instaladas:
  - Python 3.12.10;
  - PostgreSQL 16.15, pelo zip oficial da EDB com cache, porque o pacote Chocolatey levava 9 min;
  - Tesseract 5.4.0 da UB-Mannheim com `por`;
  - Chromium.

  Downloads externos são conferidos por SHA-256, e as actions ficam fixadas por SHA de commit. Ao mudar uma versão no ambiente local, mude também no `env:` do workflow. Os blocos `run:` usam o Windows PowerShell 5.1 e não podem ter acentos, porque o runner grava o script sem BOM. O log só abre com login; o passo "Resumo" publica versões e placar dos testes numa anotação, que a API pública (`/check-runs/<job>/annotations`) lê sem autenticação.

## Arquitetura-alvo (ver `docs/planejamento/05-arquitetura.md`)

Monolito Django 5.2 modular + DRF + PostgreSQL. Templates Django + HTMX + Chart.js, com Tailwind via CLI standalone (sem Node). Escolhas por rodar nativo no Windows: **Django-Q2** com broker ORM no lugar de Celery/Redis, **Waitress** no lugar de Gunicorn, **ReportLab** no lugar de WeasyPrint e **pypdfium2 + pytesseract** no lugar de OCRmyPDF/Poppler.

Princípios que atravessam vários módulos:
- **Estrutura:** apps Django em `apps/<nome>` (contas, academico, importacao, notas, analytics, paineis, relatorios, api, auditoria, ops). `dominio/regras` (Regimento) e `dominio/estatistica` são **funções puras, sem Django**, com `Decimal`, e não podem importar `django`. Cada regra cita o artigo do Regimento e lê os limiares de `ParametroRegra`, que tem a flag `confirmada`.
- **Escopo de dados central:** toda consulta de domínio (views, API, exportações) passa por uma única política de escopo. Professor vê só os próprios diários; Coordenador, os diários do curso; Admin, tudo. Não existe perfil "Aluno": o "dashboard do aluno" é um painel sobre o aluno, visto por professor e coordenador.
- **Importação versionada:** cada PDF gera uma nova versão (nada é sobrescrito); a versão vigente só muda após confirmação do professor; hash SHA-256 evita duplicatas. O pipeline roda em tarefas Django-Q2: texto via pdfplumber, OCR como fallback.
- Toda saída analítica (risco, ranking, predição, recomendação) é **estimativa** com motivo explicado. O sistema nunca grava resultado acadêmico oficial, porque a decisão é do Conselho de Classe.
- Auditoria só de inserção (`EventoAuditoria`) desde a E1.

## Formato do boletim SUAP (fixture de referência: `docs/referencias/boletins/exemplo_boletins.pdf`)

PDF com camada de texto. Cabeçalho por rótulos: `Curso:`, `Diário:` (`70764 - TIN.0054 - Nome - Médio [67 h/80 Aulas]`), `Ano/Período Letivo:`, `Aulas Ministradas:`. Colunas: `# | Matrícula (12 dígitos) | Nome | T. Faltas | % Freq. | Situação | E1..E4 (N, F) | MD | NAF (N, F) | MFD/Conceito`. A tabela continua na página 2 sem repetir o cabeçalho. `-` significa ausente, não zero. Alunos `Cancelado` ficam fora das estatísticas. Os 4 bimestres vêm no mesmo PDF; o bimestre informado no upload é o "corte". **Não há** nota de recuperação bimestral separada nem notas por avaliação. Análise completa em `docs/planejamento/15-analise-boletim-exemplo.md`.

## Regras do Regimento mais usadas (Regimento Didático Integrado 2024)

- Notas de 0 a 100. MB = média aritmética das avaliações; MA = (MB1+MB2+MB3+MB4)/4 (Art. 55).
- Recuperação bimestral se MB < 70; prevalece a maior nota (Art. 63).
- Aprovado: MA ≥ 70 e frequência ≥ 75% da carga horária **total do ano** (Art. 88). Avaliação Final se 40 ≤ MA < 70 (MA = 40 incluída: PRC-02). MA < 40 em até 3 componentes também tem AF, com a nota mínima do Anexo 01.
- MF = (6·MA + 4·AF)/10, aprovado com MF ≥ 50 (Art. 91).
- Alerta de Conselho de Classe quando mais de 30% da turma tem nota da etapa < 70 (Art. 64, interpretação PRC-05).
- Arredondamento: os valores do boletim são oficiais. O recálculo só confere, usando meio para o par (*half-even*), comportamento observado no SUAP (PRC-01).
