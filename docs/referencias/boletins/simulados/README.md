# Boletins simulados

Boletins **fictícios** para testar e demonstrar a importação (E3). Foram feitos sobre o próprio boletim de exemplo do SUAP (`../exemplo_boletins.pdf`): cabeçalho, logo, grade, fonte e rodapé são os do original. Mudam só os valores das células, a linha "Diário:" e as "Aulas Ministradas".

Os alunos são os mesmos do boletim de exemplo (nomes fictícios), em todas as disciplinas, como numa turma de verdade. Os diários 70765, 70768 e 70771 e os códigos de disciplina deles foram inventados.

## Disciplinas

| Diário | Disciplina | Carga | No boletim completo |
|---|---|---|---|
| 70764 | Análise e Projeto de Sistema (TIN.0054) | 67 h / 80 aulas | Notas do original: 29 aprovados (3 pela Avaliação Final), 3 cancelados |
| 70765 | Programação para Web (TIN.0055) | 67 h / 80 aulas | 29 aprovados (3 pela AF), 3 cancelados |
| 70768 | Banco de Dados (TIN.0052) | 67 h / 80 aulas | 28 aprovados, 1 reprovado (5 na AF), 3 cancelados |
| 70771 | Matemática III (TIN.0031) | 133 h / 160 aulas | 26 aprovados, 3 reprovados (12 na AF), 3 cancelados |

## Arquivos de cada disciplina

| Arquivo | O que tem | Bimestre a informar no envio |
|---|---|---|
| `..._ate-o-1o-bimestre.pdf` | Só a E1; E2 a E4 vazias; situação "Cursando"; aulas ministradas = 1/4 do total | 1º |
| `..._ate-o-2o-bimestre.pdf` | E1 e E2 (as mesmas notas do arquivo anterior) | 2º |
| `..._ate-o-3o-bimestre.pdf` | E1, E2 e E3 | 3º |
| `..._completo.pdf` | Os 4 bimestres, MD, Avaliação Final, MFD e situação final | 4º |
| `..._notas-faltando.pdf` (1º, 2º e 3º) | Igual ao arquivo do mesmo bimestre, mas com alunos sem nota ("-"): nº 3 e 12 na E1; nº 8 e 27 na E2; nº 12 e 20 na E3 | o do arquivo |

Antes do 4º bimestre, MD, NAF e MFD aparecem como "-", e a frequência é calculada sobre as aulas dadas até ali. É uma suposição sobre como o SUAP mostra um diário em andamento: confira com um boletim real do meio do ano.

Enviar em ordem (1º, 2º, 3º, completo) cria as versões 1, 2, 3 e 4 do diário, e cada uma precisa ser confirmada.

## Como foram gerados

`tests/apoio/boletins_simulados.py`. As notas das outras disciplinas partem das de Análise e Projeto de Sistema, com variação fixa por disciplina (o resultado é sempre o mesmo). MD, MFD e frequência seguem as contas do SUAP: arredondamento meio para o par (PRC-01) e MFD = (6·MD + 4·NAF)/10 (Art. 91). Para gerar de novo:

```powershell
.\.venv\Scripts\python -m tests.apoio.boletins_simulados --saida docs\referencias\boletins\simulados
```

O teste `tests/apoio/test_boletins_simulados.py` confere se o leitor do sistema extrai exatamente os valores gerados, sem nenhum erro ou aviso na validação.
