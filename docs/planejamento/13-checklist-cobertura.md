> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 14. Checklist final de cobertura (revisão do §14 do pedido)
- [x] Todos os IDs incluídos (32/32, conferidos na matriz).
- [x] Todos vinculados a uma etapa (IDs 15–32 com etapa concreta e motivo).
- [x] Dependências coerentes (E0→E10; reordenação Dados↔Importação e auditoria antecipada justificadas).
- [x] TCC usado para compreender o sistema original (seção 3), sem reaproveitar código.
- [x] Código inspecionado: não existe; o ambiente foi diagnosticado.
- [x] Regras do Regimento com artigo/parágrafo (RN-01…RN-23).
- [x] Regras não confirmadas sinalizadas (PRC-01…PRC-18) e divergências registradas (DIV-01…DIV-09).
- [x] Todas as funcionalidades têm entregável e critério de aceitação (matriz).
- [x] Testes previstos por tipo e por ID, com casos de borda.
- [x] Funcionalidades complementares com alocação concreta.
- [x] A sequência permite desenvolver, validar e implantar de forma incremental.

## Verificação (como validar este plano e, depois, cada etapa)
- **Do plano:** o usuário revisa as seções 5 (regras/PRC), 7 (ordem) e 9 (matriz) e responde às PRC bloqueadoras.
- **De cada etapa:** `.\.venv\Scripts\python -m pytest` verde (PostgreSQL local) + testes de interface Playwright da etapa + checklist de aceitação da etapa preenchido com evidências em `docs/evidencias/E<n>.md`. Nenhuma etapa é declarada concluída sem esse registro.
