# Planejamento completo — SUAP V2 (análise estatística de boletins SUAP para docentes)

> Escrito para: equipe de desenvolvimento e orientadores do projeto (IFPB) que vão validar o plano antes da implementação.
> Data da análise: 23/10/2026. Nenhum código foi escrito ou executado. Nenhum teste foi executado.

## Indice

- [Resumo executivo](00-resumo-executivo.md)
- [Fontes efetivamente analisadas](01-fontes.md)
- [Diagnóstico técnico do código e do ambiente](02-diagnostico.md)
- [Inventário completo das funcionalidades (tabela original)](03-inventario-funcionalidades.md)
- [Regimento Didático (IFPB, 2024): regras de negócio identificadas](04-regimento-regras-de-negocio.md)
- [Arquitetura](05-arquitetura.md)
- [Plano de desenvolvimento em etapas](06-plano-etapas.md)
- [Detalhamento das tarefas por etapa](07-tarefas-por-etapa.md)
- [Matriz de rastreabilidade (32/32 IDs)](08-matriz-rastreabilidade.md)
- [Plano de testes e critérios de aceitação](09-plano-de-testes.md)
- [Riscos, dependências e pendências](10-riscos-pendencias.md)
- [Estimativas relativas de esforço](11-estimativas.md)
- [Critérios gerais de conclusão do projeto](12-criterios-conclusao.md)
- [Checklist final de cobertura (revisão do §14 do pedido)](13-checklist-cobertura.md)
- [Decisões sobre PRC-01, 02, 03 e 05 (25/10/2026)](14-decisoes-pendencias.md)
- [Análise do boletim de exemplo do SUAP](15-analise-boletim-exemplo.md)
- [Diretrizes de UI/UX: skill UI/UX Pro Max](16-diretrizes-ui-ux.md)
- [Plano completo em arquivo unico](PLANEJAMENTO-COMPLETO.md) (versão de 23/10/2026; as decisões posteriores estão nos documentos 14 e 15)
- Evidências por etapa: [../evidencias/](../evidencias/)

## 0. Contexto e ação imediata após aprovação

**Por que este plano existe.** O TCC de 2025 (IFPB Campus Itaporanga) deixou um protótipo Django que lê um único boletim por vez, sem banco de dados, sem login e sem histórico. A Tabela de Funcionalidades define 32 requisitos para o SUAP V2. Eles devem ser implementados **com código novo, do zero**, respeitando o Regimento Didático dos Cursos Técnicos Integrados (IFPB, 2024).

**Decisões já tomadas pelo usuário (23/10/2026):**
| Decisão | Escolha |
|---|---|
| Stack | Django monolito modular: Python 3.12 + Django 5.2 LTS + DRF + PostgreSQL 16 + Django-Q2 (fila no próprio PostgreSQL) + Tesseract; frontend com templates Django + HTMX + Chart.js |
| Ambiente | **Instalação nativa no Windows** (corrigido pelo usuário em 23/10/2026; substitui Docker/WSL2): Python, PostgreSQL, Tesseract e Git instalados via winget; virtualenv `.venv`; PostgreSQL como serviço do Windows |

**Adequações técnicas decorrentes da instalação nativa no Windows:**
| Componente | Problema no Windows | Escolha |
|---|---|---|
| Fila assíncrona | Celery não tem suporte oficial no Windows desde a versão 4.0 | **Django-Q2** com broker ORM (PostgreSQL): sem Redis, com agendamento nativo (usado no backup) |
| Servidor WSGI | Gunicorn não roda no Windows | **Waitress** (puro Python); o código fica agnóstico ao servidor, então Gunicorn continua possível se a produção for Linux |
| PDF de relatórios | WeasyPrint exige GTK/Pango | **ReportLab** (wheel puro) + matplotlib para os gráficos |
| OCR | OCRmyPDF exige Ghostscript/qpdf | **pypdfium2** (wheel, renderiza páginas sem Poppler) + **pytesseract** + Tesseract UB-Mannheim com idioma `por` |
| Cache/sessões | Sem Redis | Sessões no banco; cache local em memória ou no banco |
| ID 20 "Dashboard do aluno" | Painel **sobre** um estudante, acessado apenas por Professor (das próprias turmas) e Coordenador (do curso). Não se cria perfil "Aluno". |
| Boletins reais | Ainda não há. O parser começa com fixtures sintéticos; a Etapa 3 só é aceita com amostras reais anonimizadas. |

**Ação imediata após aprovação (pedido do usuário: "salve o que estamos fazendo na pasta PROGRAMA SUAP"):**
1. Criar `C:\Users\Pichau\Downloads\PROGRAMA SUAP\docs\planejamento\` (hoje não existe, portanto não há risco de sobrescrita) e salvar este planejamento dividido em arquivos Markdown:
   `00-resumo-executivo.md`, `01-fontes.md`, `02-diagnostico.md`, `03-inventario-funcionalidades.md`, `04-regimento-regras-de-negocio.md`, `05-arquitetura.md`, `06-plano-etapas.md`, `07-tarefas-por-etapa.md`, `08-matriz-rastreabilidade.md`, `09-plano-de-testes.md`, `10-riscos-pendencias.md`, `11-estimativas.md`, `12-criterios-conclusao.md`, `13-checklist-cobertura.md` e um `README.md` com índice.
2. Registrar na memória do projeto as decisões acima e as pendências de regra (PRC).
3. **Não iniciar a Etapa 0** antes de o usuário validar o planejamento e responder às pendências bloqueadoras (seção 11).

---
