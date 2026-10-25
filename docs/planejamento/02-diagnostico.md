> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 3. Diagnóstico técnico do código e do ambiente

**Código existente:** nenhum. A pasta `.claude\skils\` é configuração do ambiente do Claude Code, não código funcional; deve ser preservada e ignorada. Situação atual de todos os 32 IDs: **ausente**.

**Ambiente (verificado em 23/10/2026, somente leitura):**
| Item | Situação |
|---|---|
| SO | Windows 10 Pro 19045; i5-8500; 15,9 GB RAM; 56,6 GB livres em C: |
| Python | Não instalado (apenas o atalho da Microsoft Store) |
| Node, Git, Docker, PostgreSQL, Redis, Tesseract, Poppler | Não instalados |
| WSL | Só o stub; nenhuma distribuição instalada |
| Virtualização de firmware | Habilitada (permite WSL2 + Docker Desktop) |
| winget | Disponível |
| VS Code | Instalado |

**Consequência:** a Etapa 0 começa pela instalação nativa (winget) de Python 3.12, PostgreSQL 16, Tesseract (UB-Mannheim) com o idioma português e Git, o que exige a autorização do usuário porque altera o sistema. O atalho "python" da Microsoft Store deve ser desativado em *Aliases de execução do aplicativo*. Hardware e disco são suficientes para a stack nativa (sem Redis, Docker ou Poppler).

**O que o TCC informa sobre o sistema original (referência funcional, não código):** fluxo de upload de PDF + escolha do bimestre → pdfplumber → pandas (filtros: matrícula com 12 dígitos, sem "cancelado", sem células vazias) → média, mediana, desvio-padrão (`.std()` do pandas, ou seja, amostral), mínimo e máximo, faixas de desempenho → histograma, barras ordenadas e pizza → PDF com ReportLab. Limitações declaradas (TCC §5.4 e §6): dependência do layout, uma turma por envio, processamento síncrono, sem persistência nem histórico, poucos indicadores. Melhorias propostas (§5.5): persistência, Celery+Redis, API REST, dashboards, parser robusto com OCR de fallback, validação quantitativa do parser e do risco, privacidade (HTTPS, autenticação, anonimização). Todas essas melhorias estão cobertas por IDs da tabela.
