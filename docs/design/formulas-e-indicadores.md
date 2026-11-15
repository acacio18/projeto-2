# Fórmulas, regras e indicadores (E4)

Como o SUAP V2 calcula cada número que mostra. Para cada um, o texto diz de onde vem (artigo do Regimento Didático dos Cursos Técnicos Integrados, IFPB 2024, ou decisão registrada em [14-decisoes-pendencias.md](../planejamento/14-decisoes-pendencias.md)) e onde está no código.

As regras ficam em `dominio/regras` e a estatística em `dominio/estatistica`. São funções puras, sem Django, com `Decimal`. Os limiares vêm de `notas.ParametroRegra` (`apps/analytics/parametros.py`).

## Princípios

- **O boletim é oficial.** MD, NAF, MFD, faltas e frequência lidos do PDF não são substituídos. O sistema só confere as contas e aponta diferenças (aviso na importação).
- **Sem arredondamento próprio** (PRC-01, decisão de 14/11/2026). O Regimento não define arredondamento. As contas do sistema são exatas: um 69,5 continua abaixo de 70. Na tela, os números aparecem com até 2 casas.
- **Nota ausente não é zero.** "–" fica fora das contas e é contado à parte ("Sem nota").
- **Estimativa, não resultado.** A situação projetada nunca diz "Reprovado". Quem decide é o Conselho de Classe (Arts. 51, 56 e 92 §2), e cada situação traz o motivo e o artigo.
- **Interpretações.** Onde o Regimento é ambíguo, vale a leitura mais favorável ao estudante e coerente com o texto (decisão do usuário, 14/11/2026).
- **Só até o corte.** Entram só as etapas até o bimestre informado no envio (PRC-17). Com corte antes do 4º bimestre, MD, AF e MFD do boletim não são usadas.
- **Quem fica de fora:** alunos cancelados ficam fora de tudo. Os marcados "fora de rankings e comparações" (Art. 72) ficam fora das estatísticas e do ranking, mas mantêm a sua situação e a sua frequência.

## Regras do Regimento (`dominio/regras`)

| Regra | Fórmula | Fonte | Código |
|---|---|---|---|
| Média anual (MA) | (N1 + N2 + N3 + N4) / 4, só com as 4 etapas lançadas | Art. 55 II | `medias.media_anual` |
| Recuperação bimestral | nota da etapa < 70 | Art. 63 | `medias.precisa_de_recuperacao` |
| Nota registrada | maior entre a média bimestral e a recuperação | Art. 63 §1 | `medias.nota_registrada` |
| Rendimento satisfatório | nota da etapa ≥ 70 | Art. 64; PRC-05 | `medias.rendimento_satisfatorio` |
| Média final (MF) | (6·MA + 4·AF) / 10 | Art. 91 | `medias.media_final` |
| Nota mínima na AF | ⌈(500 − 6·MA) / 4⌉; sem nota possível se passar de 100 | Art. 89 §1, Anexo 01 | `medias.nota_minima_na_avaliacao_final` |
| Limite de faltas | 25% das aulas previstas (parte inteira) | Art. 77 | `frequencia.faltas_permitidas` |
| Presença | (aulas − faltas) / aulas × 100 | Arts. 88 e 89 | `frequencia.percentual_de_presenca` |
| Frequência global | soma de aulas e faltas de todos os diários da turma no ano | Art. 88; PRC-03 | `frequencia.frequencia_global` |

A fórmula da nota mínima na AF reproduz os 53 pontos do Anexo 01 (MA 69 → 22 … MA 17 → 100). O teste `test_nota_minima_na_af_reproduz_o_anexo_01` confere a tabela inteira, transcrita do PDF do Regimento.

### Situação projetada de um componente (`situacao.situacao_do_componente`)

| Situação | Quando | Artigos |
|---|---|---|
| Cancelado | matrícula cancelada no SUAP | — |
| Em curso | ainda falta alguma das 4 notas | Art. 55 II |
| Risco de retenção | frequência **global** do ano < 75% (só quando todos os diários da turma estão importados) | Arts. 88 e 94 I |
| Aprovação projetada | MA ≥ 70 | Art. 88 |
| Aprovação projetada após a AF | fez a AF e MF ≥ 50 | Art. 91 |
| Conselho de Classe Final | fez a AF e MF < 50 | Arts. 91 e 92 |
| Avaliação Final | 40 ≤ MA < 70 (MA = 40 incluída, PRC-02), com a nota mínima | Arts. 89 e 91, Anexo 01 |
| Avaliação Final (média abaixo de 40) | 17 ≤ MA < 40: tem AF se estiver assim em até 3 componentes | Art. 89 §1, Anexo 01 |
| Conselho de Classe do 4º bimestre | MA < 17: nem 100 na AF chega à MF 50 | Art. 89 §2 |

### Situação do estudante no ano (`situacao.situacao_do_estudante`)

Junta todos os componentes. Os componentes optativos não contam (Art. 68).

| Situação | Quando |
|---|---|
| Risco de retenção | MA < 40 em mais de 6 componentes (Art. 94 II), MF < 50 em mais de 3 (Art. 94 III) ou frequência global baixa |
| Conselho de Classe do 4º bimestre | MA < 40 em 4 a 6 componentes, ou algum componente sem nota possível na AF (Art. 89 §2) |
| Conselho de Classe Final | MF < 50 em até 3 componentes, com possível Progressão Parcial (Arts. 92 e 93) |
| Em curso, AF ou aprovação | a pior situação restante entre os componentes |

A tela do diário mostra a situação **do componente**. A do estudante no ano depende de todos os diários da turma e entra nos painéis (E6).

## Estatística (`dominio/estatistica/descritiva.py`)

| Indicador | Definição |
|---|---|
| Alunos com nota / Sem nota | notas presentes / "–" |
| Média | soma / n |
| Mediana, 1º e 3º quartis | método inclusivo: posição (n − 1)·p com interpolação linear, igual ao QUARTIL.INC do Excel e ao padrão do numpy |
| Moda | valores mais frequentes; "não há" quando nenhum se repete; com mais de 3 empatados, a tela mostra quantos são |
| Variância e desvio-padrão | **populacionais** (÷ n): a turma é a população, não uma amostra (PRC-10) |
| Mínima, máxima, amplitude, IQR | — |
| Coeficiente de variação | desvio / média × 100. Leitura: até 15% homogênea, até 30% dispersão média, acima disso heterogênea (convenção usual em estatística) |
| % com 70 ou mais / % abaixo de 40 | sobre os alunos com nota |
| Faixas de desempenho | Crítica [0, 40), Mediana [40, 70), Boa [70, 86), Excelente [86, 100] (PRC-06) |
| z-score | (nota − média) / desvio; vazio se todos tiraram o mesmo |
| Posição (ranking, ID 22) | ranking denso: maior nota em 1º, empates na mesma posição, sem pular números. Só para professores e coordenação |

A coluna de referência é a MD do boletim quando o corte é o 4º bimestre. Antes disso, é a média das notas lançadas até o corte.

## Alerta para o Conselho de Classe (Art. 64)

Por etapa: alunos com nota < 70 / alunos com nota. O alerta aparece quando a proporção passa de 30% (30% exatos não disparam).

## Índice de recuperação (ID 24, `dominio/estatistica/recuperacao.py`)

O boletim não traz a nota da recuperação bimestral separada, só a nota já registrada (Art. 63 §1). Por isso o índice mede as recuperações que o boletim deixa ver:

- **Entre bimestres:** para cada aluno e cada etapa k com nota < 70 seguida de uma etapa k+1 lançada, conta se a nota k+1 chegou a 70. O índice é recuperados / casos, e o ganho médio é a média de (nota k+1 − nota k).
- **Na Avaliação Final:** dos que fizeram a AF, quantos chegaram à MF 50. O ganho médio é a média de (MFD − MD).

## Frequência na tela

- "Faltas até o limite" = 25% das aulas previstas no diário − faltas até o corte.
- Alerta (amarelo) quando as faltas já passaram da metade do permitido; erro (vermelho) quando passaram do limite.
- Aulas dadas: as "Aulas Ministradas" do boletim. Com corte antes do 4º bimestre num boletim completo, contam as aulas previstas proporcionais ao corte.
- As faltas são as brutas do boletim, porque abonos e justificativas (Arts. 78 a 84 e 94 §1) não aparecem nele.

## Guarda dos resultados

`apps/analytics/servicos.indicadores_da_versao` calcula na primeira vez que a versão é aberta e guarda em `SnapshotIndicadores`. A assinatura reúne três coisas, e um snapshot novo é criado sempre que uma delas muda:
- a versão do cálculo;
- os limiares e as confirmações;
- os alunos fora das comparações.

Os snapshots antigos ficam como histórico do que foi mostrado.
