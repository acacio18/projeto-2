> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 11. Riscos, dependências e pendências

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Layout real do boletim diferente do suposto (sem amostras) | Alta | Alto | Perfis de layout plugáveis; aceite da E3 condicionado a amostras reais; confirmação humana |
| Erro de OCR em dígitos altera notas | Média | Alto | OCR só como fallback, com confiança exibida e revisão obrigatória |
| Vazamento de dados de estudantes (menores) | Média | Muito alto | Escopo central, testes de matriz, minimização, auditoria, HTTPS, PRC-14 |
| Estimativas tomadas como decisão oficial | Média | Alto | Rótulos RN-21, explicação dos motivos, nenhuma "situação final" gravada |
| Regras ambíguas (PRC-01…05) | Alta | Médio | Parametrização + selo "pendente"; validação com CCA/DDE |
| Diferenças entre o ambiente nativo Windows de dev e o servidor de produção | Média | Médio | Dependências fixadas; código agnóstico ao servidor WSGI; sem dependências nativas além do PostgreSQL e Tesseract; script de verificação do ambiente |
| Django-Q2 com broker ORM limita a vazão de tarefas | Baixa | Baixo | O volume esperado (boletins de um campus) é baixo; trocar o broker é configuração, não reescrita |
| Infraestrutura de produção indefinida | Média | Médio | PRC-13; aplicação portável Windows/Linux |
| Volume de trabalho para uma equipe pequena | Média | Médio | Etapas incrementais, cada uma entregando valor utilizável |

**Pendências bloqueadoras por etapa:** E0 → autorização para instalar ferramentas. E3 (aceite) → PRC-08 (amostras) e PRC-17. E4/E5 (validação de negócio) → PRC-01…07, 10. E8 → PRC-11. E10 → PRC-13, PRC-14. E5 (recomendações) → PRC-15.
