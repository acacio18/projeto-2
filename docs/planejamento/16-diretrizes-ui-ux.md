> Parte do Planejamento SUAP V2. Índice: [README.md](README.md)

# 16. Diretrizes de UI/UX: uso obrigatório da skill "UI/UX Pro Max" (25/10/2026)

**Instrução do usuário:** na geração do programa, seguir a skill **UI/UX Pro Max** presente na pasta `.claude`. A geração **ainda não foi autorizada**.

## Situação da skill no projeto
- Está em `PROGRAMA SUAP\.claude\skils\ui-ux-pro-max.zip`, compactada e em uma pasta chamada `skils` (sem o "l"). A skill espera estar descompactada em `.claude/skills/ui-ux-pro-max/`.
- Conteúdo: `SKILL.md`, 20 tabelas CSV (estilos, paletas, tipografia, gráficos, diretrizes de UX, 9 stacks) e 3 scripts Python (`search.py`, `core.py`, `design_system.py`).
- **Revisão de segurança dos scripts (25/10/2026):** usam só a biblioteca padrão (`csv`, `json`, `re`, `pathlib`, `argparse`, `math`, `collections`), apenas leem os CSVs da própria pasta, não acessam rede, não executam processos e não gravam arquivos. Serão executados com `python -I` (modo isolado).
- **Ação pendente de autorização:** descompactar a skill em `PROGRAMA SUAP\.claude\skills\ui-ux-pro-max\`, mantendo o zip original.

## Como a skill entra em cada etapa

| Etapa | Telas/artefatos visuais | Uso da skill |
|---|---|---|
| Antes da primeira tela (início da E1) | Design system do SUAP V2 | **Passo 2 obrigatório da skill:** `search.py "<consulta>" --design-system -p "SUAP V2" -f markdown`, com a saída salva em `docs/design/design-system.md` e revisada pelo usuário antes de qualquer template |
| E1 | Login, cadastro de professores, layout base | Busca `--stack html-tailwind` (formulários, layout responsivo); domínio `ux` (acessibilidade, foco, erros de formulário) |
| E3 | Upload, progresso da importação, pré-visualização e confirmação, lote | Domínio `ux` (estados de carregamento, botões desabilitados durante operações assíncronas, mensagens de erro junto ao campo) |
| E6 | Painéis por perfil, painel da turma, painel do aluno, histórico | Domínio `chart` (tipo de gráfico por tipo de dado, paletas acessíveis, tabela alternativa ao gráfico); domínio `style` e `product` para dashboard |
| E7 | Relatórios PDF/Excel | Mesmas paleta e tipografia do design system (coerência visual) |

**Consulta inicial proposta para o design system** (Passo 1 da skill: produto, setor, palavras-chave e stack):
- Produto: dashboard / painel administrativo de análise de dados.
- Setor: educação (learning analytics, desempenho escolar).
- Palavras-chave: profissional, institucional, acessível, denso em dados, sóbrio.
- Stack: `html-tailwind` (padrão da skill, compatível com templates Django + HTMX).
- Comando previsto: `python -I .claude\skills\ui-ux-pro-max\scripts\search.py "education analytics dashboard admin panel professional accessible data-dense" --design-system -p "SUAP V2" -f markdown`

## Ajustes que a skill traz ao plano (a confirmar quando a geração for autorizada)
1. **CSS:** adotar **Tailwind CSS**, a stack padrão da skill. Para manter a instalação nativa sem Node.js, usar o **executável standalone do Tailwind CLI** (um binário único para Windows) no build dos estilos.
2. **Ícones:** SVG de um único conjunto (Lucide ou Heroicons), embutidos nos templates; **proibido usar emoji como ícone**.
3. **Gráficos:** Chart.js continua previsto, mas o tipo de cada gráfico seguirá o domínio `chart` da skill; todo gráfico terá **tabela alternativa** acessível.
4. **Temas:** modo claro e modo escuro, com contraste mínimo de 4,5:1 nos dois.
5. **Responsividade:** testar em 375, 768, 1024 e 1440 px, sem rolagem horizontal.
6. **Movimento:** transições de 150–300 ms; respeitar `prefers-reduced-motion`.
7. **Critério de aceitação novo:** o **Pre-Delivery Checklist** da skill (qualidade visual, interação, claro/escuro, layout e acessibilidade) passa a fazer parte do aceite das etapas E1, E3, E6 e E7, com evidência registrada em `docs/evidencias/`.

## Decisão pendente
- **Identidade visual:** usar as cores e o logotipo do IFPB (sistema institucional) ou a paleta recomendada pela skill? Proposta: rodar o design system da skill e ajustar a cor primária à identidade do IFPB, mantendo os contrastes exigidos pela skill. Decisão do usuário/coordenação.
