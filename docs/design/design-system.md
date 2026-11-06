# Design system do SUAP V2

> Gerado no início da E1 (06/11/2026) com a skill **UI/UX Pro Max** (`.claude/skills/ui-ux-pro-max/`) e com as cores do **Manual de Aplicação da Marca IF**. Este documento é revisado pelo usuário **antes de qualquer tela** (doc 16 do planejamento).

## 1. Como foi gerado

**Passo 2 da skill (obrigatório):**

```
python -E -s .claude\skills\ui-ux-pro-max\scripts\search.py "education analytics dashboard admin panel professional accessible data-dense" --design-system -p "SUAP V2" -f markdown
```

O script usa `-E -s` em vez de `-I`, porque o modo isolado impede o script de importar o próprio `core.py`. Com `-E -s`, o Python ainda ignora variáveis de ambiente e pacotes do usuário. Os scripts foram revisados em 25/10/2026: só leem os CSVs da própria pasta.

| Item da skill | Resultado | Adotado? |
|---|---|---|
| Estilo | **Data-Dense Dashboard**: tabelas, cartões de indicadores, grade, pouco enfeite (WCAG AA) | **Sim** |
| Padrão de página | "AI Personalization Landing" | Não: é padrão de landing page de marketing, e o SUAP V2 é um sistema interno com login |
| Cores | azul `#3B82F6` + laranja `#F97316` | **Não**, por decisão do usuário (26/10/2026): cores do IFPB (seção 2) |
| Tipografia | Fira Code + Fira Sans ("Dashboard Data") | Substituída; ver seção 4, **decisão pendente** |
| Efeitos | tooltips, destaque de linha ao passar o mouse, filtros com transição, indicadores de carregamento | Sim |
| Antipadrões | design ornamentado; tela sem filtros | Sim |

**Buscas complementares:**

| Busca | Resultado aproveitado |
|---|---|
| `--domain product "education school learning"` | Recomenda claymorphism e cores lúdicas, que servem a apps para alunos, não a um painel docente denso em dados; descartado |
| `--domain typography "professional readable government institutional dashboard"` | Par **Corporate Trust** (Lexend + Source Sans 3), indicado para governo e acessibilidade |
| `--domain ux "form validation error focus accessibility"` e `--domain web "login form password input label"` | Regras da seção 6 |

## 2. Cores oficiais (fonte)

**Manual de Aplicação da Marca IF, edição 2015**, instituído pela Portaria Setec/MEC nº 31, de 15/09/2015, página 14. O PDF foi baixado do portal do IFF em 06/11/2026 (SHA-256 `6261343f…cd316e8`). Os manuais do IFPR e do IFMT reproduzem os mesmos valores. Não foi encontrado um manual próprio do IFPB com outras cores; os Institutos Federais seguem esse manual nacional.

| Cor | RGB | HEX (publicado) | CMYK | Pantone | Significado no manual |
|---|---|---|---|---|---|
| Verde | R50 G160 B65 | `#2f9e41` | C75 M0 Y100 K15 | 362 C | "harmonia e integração na rede" |
| Vermelho | R200 G25 B30 | `#cd191e` | C0 M100 Y100 K15 | 187 C | "pensamento forte, expresso e com energia" |
| Preto | R0 G0 B0 | `#000000` | K100 | Process Black C | — |

O próprio manual tem uma pequena incoerência: R50 G160 B65 dá `#32a041`, e R200 G25 B30 dá `#c8191e`. Para tela, adotamos o **HEX publicado**. A diferença é imperceptível.

O manual também define a tipografia da marca: **Open Sans**, "nas versões bold e regular" no logotipo e "na totalidade de variações" em textos complementares.

**Uso da marca:** o sistema **não reproduz o logotipo oficial** do IF/IFPB, porque o manual tem regras próprias de construção, área de proteção e usos incorretos. Usa só as cores e o nome "IFPB" em texto. Se a instituição quiser o logotipo, ele entra como arquivo oficial fornecido pela comunicação do campus.

## 3. Paleta derivada e contraste

As escalas foram geradas em OKLCH: mesma matiz da cor oficial, variando só a luminosidade e reduzindo a saturação até caber na tela. Os contrastes foram calculados pela fórmula WCAG 2.x (o script de cálculo está registrado na evidência da E1).

**Verde IF** (`500` = oficial):

| Tom | HEX | Sobre branco | Sobre fundo escuro `#0b1120` |
|---|---|---|---|
| 50 | `#e6ffe7` | 1,06 | 17,77 |
| 100 | `#d2f9d3` | 1,15 | 16,35 |
| 200 | `#a9f0ac` | 1,33 | 14,12 |
| 300 | `#6fd97a` | 1,77 | 10,65 |
| 400 | `#51bc5e` | 2,41 | **7,81** |
| **500** | **`#2f9e41`** | 3,45 | 5,46 |
| 600 | `#048428` | **4,84** | 3,89 |
| 700 | `#046d20` | **6,53** | 2,88 |
| 800 | `#015617` | 8,96 | 2,10 |
| 900 | `#013f0f` | 12,22 | 1,54 |

**Vermelho IF** (`500` = oficial):

| Tom | HEX | Sobre branco | Sobre fundo escuro |
|---|---|---|---|
| 50 | `#fef4f3` | 1,08 | 17,44 |
| 100 | `#fee7e4` | 1,18 | 15,93 |
| 300 | `#fea196` | 1,95 | 9,64 |
| 400 | `#fe6c60` | 2,79 | **6,75** |
| **500** | **`#cd191e`** | **5,59** | 3,37 |
| 700 | `#aa000f` | **7,73** | 2,44 |
| 900 | `#650106` | 13,46 | 1,40 |

**Neutros:** escala *slate*, recomendada pela skill para texto (`#0f172a` no texto e `#475569` no mínimo para texto secundário em fundo claro). Não usar cinza mais claro que `#475569` para texto.

**Status:**
- sucesso: verde IF;
- erro: vermelho IF;
- aviso: âmbar `#b45309` no claro e `#fbbf24` no escuro;
- informação: azul `#1d4ed8` no claro e `#93c5fd` no escuro.

Regra da skill: **a cor nunca é o único indicador**. Todo status leva ícone e texto. Isso vale principalmente para os níveis de risco da E5, porque verde e vermelho se confundem no daltonismo mais comum.

## 4. Tipografia — **decisão pendente do usuário**

| Opção | Títulos | Texto | A favor | Contra |
|---|---|---|---|---|
| **A (recomendada)** | Open Sans | Open Sans | É a tipografia **oficial da marca IF** (manual, p. 16); coerente com a decisão de seguir a identidade do IFPB; uma família só, o que deixa a página mais leve | Não é sugestão direta da skill |
| B | Lexend | Source Sans 3 | Par "Corporate Trust" da skill, indicado para governo e acessibilidade; Lexend foi desenhada para legibilidade | Fica fora da identidade IF |

Nos dois casos:
- fontes **hospedadas no próprio sistema** (arquivos `.woff2`, licença OFL), sem chamar o Google Fonts, por privacidade (LGPD) e para funcionar sem internet externa;
- números de tabelas e indicadores com algarismos tabulares (`font-variant-numeric: tabular-nums`);
- texto do corpo com 16 px e entrelinha 1,5;
- linhas de no máximo 75 caracteres em textos corridos.

Escala de tamanhos: 12 (legendas), 14 (tabelas densas), **16 (corpo)**, 18, 20, 24, 30 e 36 px.

## 5. Tokens (temas claro e escuro)

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `--cor-fundo` | `#f8fafc` | `#0b1120` | fundo da página |
| `--cor-superficie` | `#ffffff` | `#111a2e` | cartões, tabelas, formulários |
| `--cor-texto` | `#0f172a` | `#e2e8f0` | texto principal |
| `--cor-texto-secundario` | `#475569` | `#94a3b8` | legendas, ajuda (≥ 6,7:1 nos dois temas) |
| `--cor-borda` | `#e2e8f0` | `#1e293b` | divisórias decorativas |
| `--cor-borda-campo` | `#64748b` | `#64748b` | borda de campos (≥ 3:1, como o WCAG exige para componentes) |
| `--cor-primaria` | `#048428` (verde-600) | `#048428` | botão primário com texto branco (4,84:1) |
| `--cor-primaria-hover` | `#046d20` (verde-700) | `#046d20` | hover do botão |
| `--cor-link` | `#048428` | `#51bc5e` (verde-400) | links e texto em verde |
| `--cor-marca` | `#2f9e41` | `#51bc5e` | faixa da marca, anel de foco (≥ 3:1) |
| `--cor-erro` | `#cd191e` | `#fe6c60` | mensagens de erro, botão destrutivo (vermelho-700 no hover) |
| `--cor-erro-fundo` | `#fef4f3` | `#3b0a0a` | fundo de alerta de erro |
| `--cor-sucesso-fundo` | `#e6ffe7` | `#0d2b14` | fundo de alerta de sucesso |

O tema segue `prefers-color-scheme` e tem um botão de troca, com a preferência guardada no navegador.

## 6. Componentes e regras (skill)

- **Ícones:** SVG de um único conjunto (**Lucide**, licença ISC), 24×24, embutidos nos templates. **Nunca emoji.**
- **Foco:** anel visível de 2 px na cor `--cor-marca`, com afastamento, em todo elemento interativo. Nunca remover o contorno sem substituto.
- **Formulários:**
  - todo campo tem `<label>`; não há campo só com placeholder;
  - tipos semânticos (`email`, `password`);
  - `autocomplete` correto (`username`, `current-password`, `new-password`);
  - nunca bloquear colar;
  - erro junto ao campo, com ícone e texto, ligado por `aria-describedby`, e resumo anunciado por `role="alert"`.
- **Botões:**
  - área de toque ≥ 44×44 px e `cursor: pointer`;
  - ficam desabilitados com indicador de carregamento enquanto o envio está em andamento;
  - hover só muda cor ou sombra, sem mudar o tamanho (nada de `scale`).
- **Movimento:** transições de 150 a 300 ms só em `color`, `background-color`, `opacity` e `transform`; tudo desligado com `prefers-reduced-motion`.
- **Layout:**
  - mobile first, com teste em 375, 768, 1024 e 1440 px, sem rolagem horizontal;
  - largura máxima de conteúdo de 1280 px;
  - cabeçalho fixo sem cobrir conteúdo;
  - camadas (`z-index`) 10, 20, 30 e 50.
- **Tabelas (densas):**
  - linha com destaque no hover e cabeçalho fixo na rolagem;
  - números alinhados à direita com algarismos tabulares;
  - em telas pequenas, rolagem horizontal **só dentro da tabela**, nunca na página.
- **Link "pular para o conteúdo"** no início de cada página.
- **Pre-Delivery Checklist da skill:** aplicado e registrado na evidência de cada etapa com telas (E1, E3, E6 e E7).

## 7. Implementação do CSS — **decisão pendente do usuário**

| Opção | Como | A favor | Contra |
|---|---|---|---|
| **A (recomendada)** | CSS próprio com os tokens acima em variáveis CSS, organizado em base, layout e componentes | Nenhuma etapa de build, nenhum executável externo para baixar e rodar (no Windows e no CI), arquivo pequeno e legível | Não usa as classes do Tailwind sugeridas pela skill |
| B | Tailwind CSS pelo executável standalone (sem Node) | Stack padrão da skill (`html-tailwind`) | Exige baixar e executar um binário de terceiros a cada mudança de estilo (o modo automático do Claude Code já bloqueou executar binários baixados na E0) e manter o CSS gerado sincronizado no CI |

As regras de UX e acessibilidade da skill valem do mesmo jeito nas duas opções.
