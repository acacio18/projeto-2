# Evidência — E0, tarefa 1: instalação nativa dos programas (25/10/2026)

Autorizada pelo usuário em 25/10/2026 ("Agora você pode começar a primeira parte que é a instalação dos programas que falta").

| Programa | Versão verificada | Como foi instalado | Verificação |
|---|---|---|---|
| Git | 2.56.0.windows.3 | `winget install --id Git.Git` | `git --version` |
| Python | 3.12.10 (`C:\Users\Pichau\AppData\Local\Programs\Python\Python312\`) | `winget install --id Python.Python.3.12 --scope user` | `python --version`; `py -0p` lista 3.12 |
| Tesseract OCR | 5.4.0.20240606 (`C:\Program Files\Tesseract-OCR\`) | `winget install --id UB-Mannheim.TesseractOCR` | `tesseract --list-langs` → `eng`, `osd`, `por` |
| Idioma português do Tesseract | `por.traineddata` (14,6 MB; SHA-256 `016C6A371BB1E4C48FE521908CF3BA3D751FADE0AB846AD5D4086B563F5C528C`) | baixado de `github.com/tesseract-ocr/tessdata` e copiado para `tessdata\` (com elevação) | aparece em `--list-langs` |
| PostgreSQL | 16.15, 64-bit | `winget install --id PostgreSQL.PostgreSQL.16` (modo unattended, porta 5432) | serviço `postgresql-x64-16` em execução, início automático; `psql -U postgres -c "select version();"` OK |

**Segredo:** a senha do superusuário `postgres` foi gerada aleatoriamente e está apenas em `%USERPROFILE%\.suap_v2\postgres_superuser_password.txt`, fora do repositório. Não deve ser versionada nem copiada para o projeto.

**Ainda não feito (próximas tarefas da E0, dependem de nova autorização):**
- Tarefa 2: criar o banco e o usuário da aplicação (`suap_v2`).
- Tarefa 3: `git init`, `.gitignore`, README; definir o repositório remoto.
- Tarefas 4 a 8: virtualenv, esqueleto Django, ferramentas de qualidade, scripts, fixtures e CI.

**Observação:** desativar o alias "python" da Microsoft Store em *Configurações → Aplicativos → Aliases de execução* evita conflito em terminais antigos. Nos terminais novos, o Python instalado já é encontrado pelo PATH do usuário e pelo `py`.
