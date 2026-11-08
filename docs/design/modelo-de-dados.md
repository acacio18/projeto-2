# Modelo de dados (E2)

Diagrama entidade-relacionamento do SUAP V2 após a E2. As caixas trazem só os campos principais; a definição completa está nos `models.py` de cada app.

```mermaid
erDiagram
    Usuario ||--o{ CoordenacaoCurso : "coordena"
    Curso ||--o{ CoordenacaoCurso : "tem"
    Curso ||--o{ Turma : "tem"
    Curso ||--o{ Disciplina : "tem"
    Curso ||--o{ Diario : "tem"
    Disciplina ||--o{ Diario : "é ministrada em"
    Turma |o--o{ Diario : "agrupa (opcional)"
    Usuario |o--o{ Diario : "é professor de"
    Diario ||--o{ MatriculaDiario : "tem"
    Estudante ||--o{ MatriculaDiario : "cursa"
    Diario ||--o{ Importacao : "tem versões"
    Usuario ||--o{ Importacao : "envia / confirma"
    Importacao ||--o{ ResultadoAluno : "contém"
    MatriculaDiario ||--o{ ResultadoAluno : "em cada versão"
    ResultadoAluno ||--|{ RegistroBimestral : "4 etapas"
    Usuario |o--o{ EventoAuditoria : "fez"

    Usuario { string email UK "institucional, minúsculas"
              string perfil "PROFESSOR | COORDENADOR | ADMIN" }
    Curso { string codigo UK "SUAP, ex. 661"
            string nome }
    Turma { int ano_letivo
            int serie "1 a 4"
            string identificador "único por curso e ano" }
    Disciplina { string codigo "SUAP, ex. TIN.0054; único no curso"
                 bool optativa "Art. 68" }
    Diario { string codigo "SUAP, ex. 70764"
             int ano_letivo
             int periodo_letivo "codigo+ano+período únicos" }
    Estudante { string matricula UK "12 dígitos (PRC-09)"
                string nome "o mais recente" }
    MatriculaDiario { bool excluir_das_comparacoes "Art. 72" }
    Importacao { int numero_versao "1, 2, 3... por diário"
                 bool vigente "uma por diário"
                 string status
                 int bimestre_corte "1 a 4 (PRC-17)"
                 string sha256 "evita duplicata" }
    ResultadoAluno { string situacao
                     int total_faltas
                     decimal frequencia_percentual
                     decimal media_disciplina "MD"
                     decimal nota_avaliacao_final "NAF"
                     decimal media_final "MFD" }
    RegistroBimestral { int bimestre "1 a 4"
                        decimal nota "0 a 100; nulo = ausente"
                        int faltas }
    ParametroRegra { string chave
                     string valor
                     bool confirmada
                     date vigente_desde }
    EventoAuditoria { datetime momento
                      string tipo
                      json detalhes "antes e depois" }
```

## Regras que o banco garante

| Regra | Como |
|---|---|
| Nada é sobrescrito (IDs 6 e 19) | Cada boletim importado vira uma `Importacao`. Depois de confirmada, ela e as notas dela não mudam nem somem: o modelo recusa, e gatilhos no PostgreSQL (`notas/0002`) barram `UPDATE` e `DELETE`. Só o campo `vigente` pode mudar. |
| Uma versão vigente por diário | Índice único parcial (`diario` onde `vigente = true`), e vigente só se confirmada (`CHECK`). |
| Notas de 0 a 100 (RN-01) | `CHECK` em nota, MD, NAF, MFD e % de frequência; nulo = ausente, não zero. |
| Bimestre de 1 a 4 (RN-19) | `CHECK` no registro e no bimestre de corte. |
| Sem duplicatas | Códigos do SUAP únicos (curso; disciplina no curso; diário no ano e período; matrícula); mesmo SHA-256 no mesmo diário é recusado. |
| Coerência do diário | Disciplina e turma do mesmo curso e ano do diário; professor ativo com perfil Professor ou Coordenador (validação do modelo). |
| Auditoria só de inclusão (ID 13) | Gatilho em `auditoria_eventoauditoria` (`auditoria/0002`). |

## Por que a turma é opcional

O boletim do SUAP traz curso, diário e disciplina, mas não a turma. O diário criado a partir de um boletim fica sem turma, até a coordenação ou a administração vincular (tela "Editar diário").
