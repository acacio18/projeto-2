> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 1. Resumo executivo

O SUAP V2 será uma aplicação web em que o professor envia o PDF "Boletim de Notas do Diário" exportado pelo SUAP. O sistema extrai as notas (por texto ou OCR), guarda o resultado com histórico versionado, calcula indicadores estatísticos, aplica as regras do Regimento Didático (médias, recuperação, Avaliação Final, frequência) e apresenta painéis, alunos em risco, comparações, projeções de reprovação e recomendações pedagógicas. Também gera relatórios em PDF, Excel, CSV e JSON, expõe uma API REST documentada em Swagger, registra auditoria e será implantado em produção com HTTPS, backup e monitoramento.

O trabalho foi organizado em **11 etapas (E0–E10)**. Os 32 IDs da tabela estão alocados em etapas concretas; os IDs 15–32 ("Contínuo") não ficam adiados indefinidamente. Há **18 pendências de regra/decisão (PRC-01…PRC-18)** e **9 divergências (DIV-01…DIV-09)** que precisam de validação institucional. A principal pendência técnica é a falta de boletins reais para calibrar o parser.

Princípio orientador: o Regimento afirma que a avaliação é "processual, diagnóstica… com prevalência dos aspectos qualitativos" (Art. 51) e que as decisões finais cabem ao Conselho de Classe (Arts. 56, 89 §2, 92). Por isso o sistema **nunca registra resultado acadêmico oficial**: apresenta apenas "situação projetada", "estimativas" e "sugestões", sempre com o critério explicado.
