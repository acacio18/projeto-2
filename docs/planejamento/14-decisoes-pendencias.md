> Parte do Planejamento SUAP V2. Índice: [README.md](README.md)

# 14. Decisões sobre as pendências PRC-01, PRC-02, PRC-03 e PRC-05 (25/10/2026)

O usuário pediu que estas quatro pendências fossem resolvidas com base nas informações oficiais do IFPB.

**Limitação da pesquisa.** Em 25/10/2026 os servidores `ifpb.edu.br` e `estudante.ifpb.edu.br` recusaram conexão (ECONNREFUSED/HTTP 502). Por isso, os trechos das versões **2014** e **2024** abaixo vêm dos resultados de busca que indexam esses documentos oficiais, e não de uma leitura direta. O texto de 2024 foi conferido no PDF fornecido pelo usuário (`Regimento_didatico_-_integrado_-_2024.pdf`). A busca indica que o Regimento vigente foi aprovado pela **Resolução 44/2024-CONSUPER**. A Resolução 153/2017-CS (Regulamento do Conselho de Classe) não pôde ser aberta.

## PRC-01 — Arredondamento de médias → **RESOLVIDA por evidência do SUAP (a confirmar com mais boletins)**

- **Normas:** nem o Regimento 2024, nem a versão 2014, nem os manuais do estudante encontrados definem o arredondamento das médias escolares. A única regra de arredondamento encontrada em documento do IFPB (Edital 146/2025, processo seletivo) trata de outro assunto e não se aplica.
- **Evidência empírica (boletim oficial do SUAP, `exemplo_boletins.pdf`, diário 70764):** recalculando MD = (N1+N2+N3+N4)/4 para os 29 alunos ativos:
  - **meio para o par** (*round half to even*): **29/29** acertos;
  - meio para cima: 28/29 (falha em 82,5 → o SUAP registrou **82**, não 83).
  - Outros casos de x,5: 87,5 → 88; 79,5 → 80 (coerentes com as duas hipóteses).
  - `% Freq.` = (aulas ministradas − faltas)/aulas ministradas: 97,5% → **98%** (coerente com meio para o par).
  - MFD = (6·MD + 4·NAF)/10 confere nos 3 casos com AF (68, 51, 71). No caso de Diego, 50,6 ou 50,75 → **51**, nas duas hipóteses.
- **Decisão adotada:**
  1. Os valores **MD, NAF, MFD, T. Faltas e % Freq. lidos do boletim são os valores oficiais**. O sistema não os substitui por cálculo próprio.
  2. O recálculo interno serve só para **conferência de qualidade**. Ele usa `Decimal` com arredondamento *meio para o par* para inteiro; divergência gera **aviso** na importação (não bloqueia).
  3. Nas projeções (ID 25), a comparação com os limiares (70, 40, 50) usa a média **arredondada da mesma forma que o SUAP**, e a interface mostra também o valor exato.
  4. **Confirmação pendente:** a hipótese "meio para o par" se apoia em um único caso discriminante (82,5). Ela deve ser revalidada com mais boletins. A regra fica parametrizada (`ARREDONDAMENTO_MEDIA = HALF_EVEN`) e com o selo "confirmada por evidência, não por norma".

## PRC-02 — Média Anual exatamente 40 → **RESOLVIDA: MA = 40 tem direito à Avaliação Final, com AF mínima 65**

- O Regimento 2024 (Art. 89 caput) exige MA "inferior a 70 e superior a 40", e o §1 trata de MA "inferior a 40". O valor 40 fica sem cobertura literal.
- O **Regimento dos Cursos Técnicos Integrados de 2014** (versão anterior, oficial) dizia: "Submeter-se-á à Avaliação Final (AF) da disciplina o discente que apresentar frequência mínima de 75% da carga horária total prevista para o ano letivo e obtiver Média Anual (MA) inferior a 70 (setenta) e **igual ou superior a 40** (quarenta)".
- O **Anexo 01 do Regimento 2024** lista explicitamente **MA 40 → AF mínima 65**, coerente com MF = (6·40 + 4·65)/10 = 50.
- **Decisão adotada:** MA = 40 é tratada como elegível à AF pelo caput (sem consumir o limite de "até 3 componentes" do §1), com AF mínima 65. Fundamento: redação de 2014 + Anexo 01 de 2024. Selo: "interpretação documentada".

## PRC-03 — Frequência por componente ou global anual → **RESOLVIDA: a regra normativa é global anual; o indicador do boletim é por diário**

- **Regimento 2024:** Art. 88 (aprovação) e Art. 89 (AF): "75% … da **carga horária total prevista para o ano letivo**"; Art. 94 I (retenção): idem; Art. 77: limite de 25% de faltas "do total da carga horária estabelecida para o período letivo". A versão 2014 usa a mesma redação.
- **Contraste oficial:** o Regimento dos **Cursos Técnicos Subsequentes** fixa a frequência mínima de 75% **por componente curricular**. A diferença de redação entre as modalidades confirma que, no **integrado**, a apuração normativa é **global, sobre a carga horária total do ano letivo**.
- **O que o boletim traz:** `T. Faltas` e `% Freq.` **do diário** (por componente), com denominador nas aulas ministradas (ex.: 4 faltas em 80 aulas → 95%), e faltas por etapa (F).
- **Decisão adotada:**
  1. **Indicador por componente** (sempre disponível): o `% Freq.` do boletim, mais uma projeção de quantas faltas faltam para 25% no componente. É rotulado como **alerta precoce**, não como regra de retenção.
  2. **Frequência global anual** (regra RN-08/09/15): calculada somando faltas e aulas de **todos os diários da turma no ano**, quando todos estiverem importados. A interface mostra "cobertura: X de Y diários importados"; com cobertura incompleta, o sistema **não** emite situação baseada em frequência global.
  3. Faltas justificadas (Art. 94 §1) não aparecem no boletim: o sistema avisa que usa faltas brutas.

## PRC-05 — "Rendimento satisfatório" (Art. 64) → **ADOTADA INTERPRETAÇÃO: MB ≥ 70**

- O Regimento 2024 (Art. 64) e o de 2014 (artigo equivalente) usam "rendimento satisfatório nas avaliações bimestrais" **sem definir número**. Os regulamentos de Conselho de Classe encontrados (Guarabira; Resolução 153/2017-CS, não acessível) não trouxeram definição nos trechos obtidos.
- A âncora normativa mais próxima é o Art. 63: a recuperação bimestral é destinada a quem "não atingiu a média bimestral de 70 (setenta) pontos". Portanto, quem atinge 70 não precisa de recuperação, o que caracteriza rendimento satisfatório no bimestre.
- **Decisão adotada:** rendimento satisfatório no bimestre = **N da etapa ≥ 70**. Alerta do Art. 64 quando a proporção de alunos **ativos** (excluídos cancelados/transferidos) com N < 70 for **> 30%** (estritamente maior). Selo: "interpretação — validar com a coordenação pedagógica"; limiar parametrizado.

## Fontes consultadas
- Regimento Didático dos Cursos Técnicos Integrados ao Ensino Médio (IFPB, 2024), PDF fornecido pelo usuário; versão online: https://www.ifpb.edu.br/pro-reitoria/pre/assuntos/regulamentos/regimento-didatico-cursos-tecnicos-integrados-ao-ensino-medio.pdf/@@download/file
- Regimento Didático Cursos Técnicos Integrados (IFPB, out/2014): https://www.ifpb.edu.br/pre/assuntos/regulamentos/Arquivos/regimento-didatico-dos-cursos-tecnicos-integrados.pdf
- Regimento Didático Cursos Técnicos Subsequentes (IFPB): https://www.ifpb.edu.br/pro-reitoria/pre/assuntos/regulamentos/regimento-didatico-cursos-tecnicos-subsequentes-ao-ensino-medio.pdf/@@download/file
- Regimento do Conselho de Classe — Cursos Técnicos Integrados (IFPB Guarabira): http://editor.ifpb.edu.br/campi/guarabira/arquivos/documentos/Regimento_do_Conselho_de_Classe.pdf
- Resolução nº 153/2017-CS (Conselho de Classe; não acessível em 25/10/2026): https://www.ifpb.edu.br/orgaoscolegiados/consuper/resolucoes/2017/resolucoes-aprovadas-pelo-colegiado/resolucao-no-153/view
- Regulamentos Institucionais (lista que indica a Resolução 44/2024): https://www.ifpb.edu.br/pre/assuntos/regulamentos
- Edital nº 146/2025 (arredondamento no processo seletivo; não aplicável): https://estudante.ifpb.edu.br/media/Edital_n%C2%BA_146-2025_-_Cursos_Integrados_PSCT_2026.docx_FNKSxLe.pdf
- Boletim de exemplo do SUAP: `C:\Users\Pichau\Downloads\exemplo_boletins.pdf` (ver [15-analise-boletim-exemplo.md](15-analise-boletim-exemplo.md))
