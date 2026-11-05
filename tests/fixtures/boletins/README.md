# Boletins de teste

Material de referência para os testes do leitor de boletins (Etapa 3).

## Boletim de exemplo (nº 1)

| Item | Onde |
|---|---|
| PDF original, com camada de texto (nomes fictícios, versionamento autorizado em 25/10/2026) | [`docs/referencias/boletins/exemplo_boletins.pdf`](../../../docs/referencias/boletins/exemplo_boletins.pdf) |
| Gabarito: valores que o leitor deve extrair | [`exemplo_boletins.gabarito.json`](exemplo_boletins.gabarito.json) |
| Versões digitalizadas (só imagem), para OCR | geradas na hora por [`tests/apoio/digitalizacao.py`](../../apoio/digitalizacao.py) |

### Gabarito

Transcrição manual da imagem das páginas: cabeçalho, 32 alunos e todas as colunas. `null` corresponde a `-` no boletim (ausente, não zero). O arquivo também lista as peculiaridades do PDF que o leitor precisa tolerar (campo `observacoes`).

Os testes em [`tests/apoio/test_gabarito_exemplo.py`](../../apoio/test_gabarito_exemplo.py) conferem o gabarito de três formas:
- contra a **camada de texto** do PDF: cada linha de aluno, montada a partir do gabarito, precisa existir na página certa, e não pode haver linha de aluno a mais;
- contra o **hash SHA-256** do PDF;
- pelas **contas do boletim**: faltas por etapa somam o total; `% Freq.`, `MD` e `MFD` batem com o recálculo usando meio para o par (PRC-01).

Se o gabarito for alterado por engano, esses testes falham.

### Versões digitalizadas

| Variante | O que simula |
|---|---|
| `300dpi` | escaneamento limpo a 300 dpi, tons de cinza |
| `150dpi` | baixa resolução |
| `300dpi_inclinado` | folha torta (1,5°) com ruído de scanner |
| `300dpi_girado90` | página colocada de lado no scanner (90°) |

Os arquivos têm de 0,5 a 2,5 MB, por isso não são versionados. A geração é determinística (ruído com semente fixa), então todo teste recebe os mesmos pixels. Nos testes, use a fixture `boletim_digitalizado("300dpi")` (definida em `tests/conftest.py`). Para gerar e olhar os arquivos:

```powershell
.\.venv\Scripts\python -m tests.apoio.digitalizacao --saida C:\caminho\da\pasta
.\.venv\Scripts\python -m tests.apoio.digitalizacao --saida C:\caminho\da\pasta --variante 300dpi_inclinado
```

## Novos boletins

Um boletim real só entra no repositório com a confirmação de que os dados são fictícios ou anonimizados (PRC-14). Cada boletim novo ganha o próprio `*.gabarito.json` no mesmo formato (`"esquema": 1`).
