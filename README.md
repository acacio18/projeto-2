# SUAP V2

Sistema web de apoio a professores e coordenadores do **IFPB** (cursos técnicos integrados ao ensino médio). Ele lê o PDF "Boletim de Notas do Diário" exportado pelo SUAP e transforma as notas em estatísticas, painéis, alertas de alunos em risco, comparações entre turmas e bimestres, projeções e relatórios. Tudo segue o Regimento Didático dos Cursos Técnicos Integrados do IFPB (2024).

É uma reimplementação completa, escrita do zero, da proposta do TCC *"Automação do tratamento estatístico das notas dos alunos do IFPB pelo SUAP para docentes"* (IFPB Campus Itaporanga, 2025).

> **Aviso:** os indicadores, riscos e projeções do sistema são **apoio pedagógico e estimativas**. Eles não substituem o registro oficial no SUAP nem as decisões do Conselho de Classe.

## Situação

Em desenvolvimento: **Etapa 0, fundação técnica**. Ainda não há código da aplicação.

## Documentação

- [Planejamento completo](docs/planejamento/README.md): requisitos (32 funcionalidades), regras do Regimento, arquitetura, etapas E0–E10, matriz de rastreabilidade e plano de testes.
- [Decisões sobre regras pendentes](docs/planejamento/14-decisoes-pendencias.md)
- [Análise do boletim SUAP de exemplo](docs/planejamento/15-analise-boletim-exemplo.md); o PDF (nomes fictícios) está em [docs/referencias/boletins/](docs/referencias/boletins/)
- [Diretrizes de UI/UX](docs/planejamento/16-diretrizes-ui-ux.md)
- [Evidências por etapa](docs/evidencias/)

## Stack prevista

Python 3.12 · Django 5.2 · Django REST Framework · PostgreSQL 16 · Django-Q2 · Tesseract OCR (português) · HTMX · Chart.js · Tailwind CSS. Execução nativa no Windows, sem Docker.

## Pré-requisitos do ambiente (Windows)

- Python 3.12, PostgreSQL 16, Tesseract OCR 5 com o idioma `por` e Git.
- Os passos de instalação e execução da aplicação serão documentados aqui ao final da Etapa 0.
