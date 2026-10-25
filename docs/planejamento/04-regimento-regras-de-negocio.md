> Parte do Planejamento SUAP V2 (23/10/2026). Indice: [README.md](README.md)

# 5. Regimento Didático (IFPB, 2024): regras de negócio identificadas

Legenda: **[OBR]** = regra institucional obrigatória; **[EXP]** = critério estatístico ou exploratório (não normativo); **[PRC]** = regra pendente de confirmação.

### 5.1 Regras com suporte no texto oficial

| Cód. | Referência | O que a norma determina (fiel) | IDs afetados | Consequência no sistema | Testes que comprovam |
|---|---|---|---|---|---|
| RN-01 [OBR] | Art. 54 §3 | Avaliações expressas em notas de 0 a 100 | 3, 4, 5, 7 | Validação rejeita ou sinaliza nota < 0 ou > 100; escala fixa 0–100 nos gráficos | Unitário: −1, 0, 100, 100.01, "abc" |
| RN-02 [OBR] | Art. 55 I | MB = ΣA / n (média aritmética das avaliações realizadas) | 4, 7, 24 | Se o boletim trouxer as notas por avaliação, recalcular a MB e conferir com a MB informada (divergência = alerta de qualidade); se trouxer só a MB, usá-la | Unitário com n = 2, 3, 5 |
| RN-03 [OBR] | Art. 55 II | MA = (MB1 + MB2 + MB3 + MB4) / 4 | 7, 8, 25 | MA só é "definitiva" com 4 MB; antes disso, existe só a MA parcial/projetada (RN-21) | Unitário; caso com MB ausente |
| RN-04 [OBR] | Art. 63 caput | Avaliação de recuperação ao fim de cada bimestre para quem não atingiu MB 70 | 8, 24, 26 | Marca "elegível à recuperação bimestral" quando MB < 70 | Limites: 69,99 / 70 / 70,01 |
| RN-05 [OBR] | Art. 63 §1 | Para registro, prevalece o maior valor entre a MB e a nota de recuperação | 4, 24 | Nota registrada = max(MB, Rec); a nota pré-recuperação é guardada para o índice de recuperação | Unitário: Rec < MB, Rec > MB, Rec ausente |
| RN-06 [OBR] | Art. 63 §2 | Perde o direito à recuperação quem faltou sem justificativa a qualquer avaliação do bimestre | 24, 26 | Informação ausente no boletim → apenas texto explicativo; o sistema não infere | Teste de UI: o aviso aparece |
| RN-07 [OBR] + PRC-05 | Art. 64 | Se > 30% da turma não alcançar rendimento satisfatório nas avaliações bimestrais, as causas devem ser diagnosticadas em Conselho de Classe | 8, 21, 26 | Alerta de turma quando a proporção de "não satisfatório" > 30% (estritamente maior) | 30% exato não dispara; 30,1% dispara; turma vazia não dispara |
| RN-08 [OBR] | Art. 88 | Aprovado: MA ≥ 70 em cada componente **e** frequência ≥ 75% da CH total prevista no ano | 8, 23, 25 | Situação projetada "Aprovado" | Matriz de casos MA × frequência |
| RN-09 [OBR] | Art. 89 caput | Vai à Avaliação Final quem tem frequência ≥ 75% e 40 < MA < 70 | 8, 25 | Situação projetada "Avaliação Final" | MA 40, 40,01, 69,99, 70 |
| RN-10 [OBR] | Art. 89 §1 + Anexo 01 | MA < 40 em até 3 componentes: tem direito à AF, respeitada a nota mínima do Anexo 01 (MA 69 → AF 22 … MA 17 → AF 100) | 8, 25, 26 | Calcula a "AF mínima necessária". Com MA < 17, a aprovação na AF é matematicamente impossível (MF máx < 50) | Tabela do Anexo inteira como teste parametrizado (MA 17–69) |
| RN-11 [OBR] | Art. 89 §2 | Quem não atinge a MA mínima para AF em até 6 componentes tem a situação deliberada pelo Conselho de Classe do 4º bimestre | 8, 25 | Rótulo "Depende do Conselho de Classe"; nunca "Reprovado" | Estudante com 4–6 componentes MA < 40 |
| RN-12 [OBR] | Art. 91 | MF = (6·MA + 4·AF) / 10; aprovado se MF ≥ 50 | 25 | Calcula MF quando a AF existe; AF necessária = ⌈(500 − 6·MA)/4⌉ (confere com o Anexo 01) | Conferência fórmula × Anexo 01 em todos os 53 pontos |
| RN-13 [OBR] | Art. 92 | Conselho de Classe Final para quem fez a AF e ficou com MF < 50 em até 3 componentes | 25 | Rótulo "Conselho de Classe Final" | 3 vs 4 componentes |
| RN-14 [OBR] | Art. 93 | Progressão Parcial: até 3 componentes em reprovação após AF e Conselho Final | 25, 26 | Rótulo informativo "Possível Progressão Parcial (decisão do Conselho)" | Casos limite |
| RN-15 [OBR] | Art. 94 I–V | Retenção: frequência < 75%; MA < 40 em mais de 3 componentes (salvo Art. 89 §2); MF < 50 em mais de 3; não realizar a AF; não aprovado nem com Progressão Parcial pelo Conselho Final | 8, 25 | "Risco de retenção" projetado (nunca resultado oficial) | Casos I–IV |
| RN-16 [OBR] + PRC-03/04 | Art. 77; Art. 94 §1 | Limite de 25% de faltas sobre a CH do período; faltas justificadas são desconsideradas na apuração da frequência para retenção | 23, 8, 25 | Frequência = 1 − faltas/CH; alerta quando a projeção de faltas ultrapassa 25% | 25% exato; CH zero; faltas > CH |
| RN-17 [OBR] | Art. 95 | Evadido: ausência não justificada > 25% da CH do período e/ou rendimento nulo em todos os componentes | 8, 23 | Rótulo "risco de evasão" (indicador; a classificação oficial é do SUAP) | Caso de rendimento nulo |
| RN-18 [OBR] | Art. 54 §8 | Mínimo de 2 avaliações por bimestre | 4 | Se o boletim trouxer as avaliações, menos de 2 = aviso de qualidade (não bloqueia) | n = 1 |
| RN-19 [OBR] | Art. 11; Art. 12 VI | Regime anual com bimestres | 3, 6, 9 | Bimestre ∈ {1, 2, 3, 4}; período = ano letivo | Bimestre 0 e 5 são rejeitados |
| RN-20 [OBR] | Art. 68 | Reprovação em língua estrangeira optativa não retém na série | 8, 25 | Disciplina com atributo "optativa"; excluída da contagem de componentes para retenção | Caso com optativa reprovada |
| RN-21 [OBR] | Art. 51; Art. 56; Art. 92 §2 | Prevalência do qualitativo; o Conselho de Classe avalia; o coordenador informa o resultado no sistema acadêmico | 8, 22, 25, 26 | Toda saída analítica traz o rótulo "estimativa/apoio, não substitui decisão do Conselho de Classe" | Teste de UI e de exportação: o rótulo está presente |
| RN-22 [OBR] | Art. 72; Art. 69 | Discentes com deficiência podem ser avaliados por portfólio e parecer descritivo | 7, 8, 22 | O sistema **não coleta** dado de deficiência (dado sensível). O professor pode marcar "excluir das estatísticas comparativas" sem informar o motivo | Teste: estudante excluído não entra no ranking/estatística, mas continua no painel individual |
| RN-23 [OBR] | Arts. 78, 80–84 | Abono de faltas, regime domiciliar e guarda religiosa | 23 | Informação ausente no boletim → o sistema mostra "faltas brutas" e avisa que justificativas não são consideradas | Teste de UI |

### 5.2 Pendências de regra (precisam de validação antes de virar regra de negócio)

| Cód. | Pendência | Informação que falta | Quem valida | Proposta provisória (configurável, marcada "não confirmada") |
|---|---|---|---|---|
| PRC-01 | Arredondamento de MB, MA e MF e casas decimais | O Regimento não define. O Anexo 01 sugere arredondamento da AF para cima | CCA/DDE do campus; conferir o comportamento do SUAP | Cálculo com `Decimal`, sem arredondar comparações; exibir 2 casas |
| PRC-02 | MA exatamente 40 | Art. 89 caput exige MA "superior a 40"; §1 trata "inferior a 40"; MA = 40 fica sem cobertura, mas o Anexo 01 lista 40 → 65 | DDE (Art. 104, casos omissos) | Tratar MA = 40 como elegível à AF com mínimo 65 (coerente com o Anexo) |
| PRC-03 | Frequência por componente ou global anual | Arts. 88, 89 e 94 falam em "CH total prevista para o ano letivo"; Art. 54 §4 registra faltas por disciplina; cada PDF contém um diário só | CCA | Indicador por componente; o global só aparece quando todos os diários da turma estiverem importados |
| PRC-04 | Art. 94 §1 remete ao "Art. 59" para faltas justificadas, mas o Art. 59 trata de reposição de avaliações (provável remissão ao Art. 78) | Correção da remissão | DDE/PRE | Seguir o Art. 78 como base |
| PRC-05 | Definição de "rendimento satisfatório" (Art. 64) | Não há número na norma | Coordenação pedagógica | MB ≥ 70 (coerente com o Art. 63) |
| PRC-06 | Faixas de desempenho do TCC (crítica/mediana/boa/excelente) | Só os cortes 40 e 70 têm âncora normativa; o 85/86 não tem | Orientador/coordenação | [0,40) / [40,70) / [70,86) / [86,100], configuráveis, rotuladas [EXP] |
| PRC-07 | Níveis de risco (ID 8) | Nenhuma norma define | Coordenação pedagógica | Ver regra de risco em 8.5 |
| PRC-08 | Layout real do boletim: colunas, faltas, nota de recuperação separada, situação | Amostras reais | Usuário/docentes | Fixtures sintéticos até chegarem amostras |
| PRC-09 | Formato da matrícula (TCC: 12 dígitos) | Confirmação | CCA | Regex configurável; o padrão aceita 12 dígitos |
| PRC-10 | Desvio-padrão populacional ou amostral; método dos quartis | O TCC usa amostral (pandas `.std()`) | Orientador (estatística) | Populacional (a turma é a população), com o rótulo "σ populacional"; quartis pelo método inclusivo (= QUARTIL.INC do Excel) |
| PRC-11 | O que é o "Desenvolvedor" do ID 12 | Não existe como perfil no ID 1 | Coordenação do projeto | Cliente de API com credencial emitida pelo Admin, sem login na interface |
| PRC-12 | Professor pode importar diário de outro professor? Diário com mais de um docente? | — | Coordenação | O diário fica vinculado a quem importou; o coordenador pode reatribuir |
| PRC-13 | Infraestrutura de produção (servidor, domínio, certificado, RPO/RTO, retenção de backup, operador) | — | DTI/TI do campus | Servidor Windows nativo (igual ao dev), mantendo o código portável para Linux |
| PRC-14 | Proteção de dados (LGPD, Lei 13.709/2018, Art. 14: dados de adolescentes) | A norma não está nos documentos fornecidos; é lei federal aplicável | Encarregado de dados do IFPB | Minimização: armazenar só matrícula, nome e notas/faltas; sem CPF, contato ou dado sensível |
| PRC-15 | Catálogo de textos das recomendações pedagógicas (ID 26) | Conteúdo pedagógico | Equipe pedagógica | Rascunho baseado nos mecanismos do Regimento (Núcleos de Aprendizagem Art. 62, recuperação Art. 63, monitoria, Conselho de Classe Art. 64) |
| PRC-16 | Vínculo coordenador ↔ curso(s) | — | Coordenação | Muitos-para-muitos, mantido pelo Admin |
| PRC-17 | Significado do "bimestre informado" no upload, já que o boletim traz os 4 bimestres | — | Usuário/docentes | Bimestre de corte = último bimestre considerado fechado; notas posteriores são ignoradas e reportadas |
| PRC-18 | Integração com a API oficial do SUAP | Fora do escopo da tabela (a entrada é PDF) | Coordenação | Não implementar; registrar como possível evolução futura |

### 5.3 Divergências entre documentos

| Cód. | Divergência | Proposta para validação |
|---|---|---|
| DIV-01 | O TCC usa faixas inconsistentes: §3.2 "0–40/41–69/70–85/86–100"; §3.3 "abaixo de 40, entre 40 e 70"; §4.3 "0–39, 40–69, 70–85, 86–100"; §5.2 "Ruim/Mediana/Boa/Excelente" | Adotar PRC-06 (intervalos semiabertos, robustos a decimais) |
| DIV-02 | TCC §3.4 exclui registros com nota ausente; o Regimento trata ausência como fato relevante (Art. 63 §2) | Nunca descartar em silêncio: o estudante fica com "nota ausente", e as estatísticas informam o n válido e quantos ficaram fora |
| DIV-03 | O TCC usa desvio amostral; a proposta é populacional | PRC-10 |
| DIV-04 | Tabela ID 3: "informa o bimestre"; o boletim do TCC traz os 4 bimestres | PRC-17 |
| DIV-05 | ID 11 lista só "Professor"; ID 2 dá ao Coordenador acesso a todas as turmas do curso | Permitir exportação também ao Coordenador, dentro do seu escopo (validar) |
| DIV-06 | Art. 94 §1 → "Art. 59" (remissão provavelmente incorreta) | PRC-04 |
| DIV-07 | Art. 89 caput × §1 em MA = 40 | PRC-02 |
| DIV-08 | Perfil "Desenvolvedor" (ID 12) inexistente no ID 1 | PRC-11 |
| DIV-09 | O sumário do Regimento cita "Língua Espanhola"; o Cap. X trata de "Línguas Estrangeiras" | Sem impacto; usar o texto do capítulo (atributo "optativa") |

**Separação obrigatória:** as regras [OBR] ficam no módulo `regras`, versionado e com referência ao artigo em cada função. Os critérios [EXP] (faixas, níveis de risco, z-score, ranking) ficam em `analytics`/`estatistica`, parametrizados. Toda regra com PRC aberta tem a flag `confirmada=False`, e a interface mostra o selo "regra pendente de confirmação institucional".
