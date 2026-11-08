"""Valores iniciais de ParametroRegra: limiares do Regimento Didático (integrado, 2024) e das PRC.

`confirmada=True` só para valores escritos na norma. Interpretações e pendências ficam com
`confirmada=False` (selo "pendente de confirmação"), conforme docs/planejamento/14-decisoes-pendencias.md.

Vigência desde 2000-01-01: são os valores do Regimento 2024 e valem também para anos anteriores, até
que se cadastre (como nova linha) um valor diferente da norma da época, se houver.
"""

import datetime

from django.db import migrations

DESDE = datetime.date(2000, 1, 1)

# (chave, valor, tipo, descrição, fundamento, confirmada)
PARAMETROS = [
    ("NOTA_MINIMA", "0", "INTEIRO", "Menor nota possível.", "Regimento 2024, Art. 54 §3", True),
    ("NOTA_MAXIMA", "100", "INTEIRO", "Maior nota possível.", "Regimento 2024, Art. 54 §3", True),
    ("NUMERO_DE_BIMESTRES", "4", "INTEIRO", "Etapas do ano letivo (regime anual).", "Regimento 2024, Arts. 11 e 12", True),
    (
        "MEDIA_RECUPERACAO_BIMESTRAL",
        "70",
        "INTEIRO",
        "Abaixo desta média bimestral (MB) o estudante tem recuperação no bimestre.",
        "Regimento 2024, Art. 63",
        True,
    ),
    ("MEDIA_APROVACAO", "70", "INTEIRO", "Média anual (MA) mínima para aprovação direta.", "Regimento 2024, Art. 88", True),
    (
        "FREQUENCIA_MINIMA_PERCENTUAL",
        "75",
        "INTEIRO",
        "Frequência mínima sobre a carga horária total do ano letivo.",
        "Regimento 2024, Arts. 88, 89 e 94 I; PRC-03 (apuração global anual)",
        True,
    ),
    (
        "MEDIA_MINIMA_AVALIACAO_FINAL",
        "40",
        "INTEIRO",
        "Média anual a partir da qual há Avaliação Final pelo caput (MA = 40 incluída).",
        "Regimento 2024, Art. 89 e Anexo 01; PRC-02 (interpretação documentada)",
        False,
    ),
    (
        "LIMITE_COMPONENTES_AF_ABAIXO_DE_40",
        "3",
        "INTEIRO",
        "Componentes com MA < 40 que ainda dão direito à Avaliação Final (nota mínima do Anexo 01).",
        "Regimento 2024, Art. 89 §1",
        True,
    ),
    (
        "LIMITE_COMPONENTES_CONSELHO_4O_BIMESTRE",
        "6",
        "INTEIRO",
        "Até quantos componentes abaixo da MA mínima a situação é deliberada pelo Conselho de Classe do 4º bimestre.",
        "Regimento 2024, Art. 89 §2",
        True,
    ),
    ("PESO_MA_MEDIA_FINAL", "6", "INTEIRO", "Peso da média anual na média final: MF = (6·MA + 4·AF)/10.", "Regimento 2024, Art. 91", True),
    ("PESO_AF_MEDIA_FINAL", "4", "INTEIRO", "Peso da Avaliação Final na média final.", "Regimento 2024, Art. 91", True),
    ("MEDIA_FINAL_APROVACAO", "50", "INTEIRO", "Média final (MF) mínima para aprovação após a AF.", "Regimento 2024, Art. 91", True),
    (
        "LIMITE_COMPONENTES_CONSELHO_FINAL",
        "3",
        "INTEIRO",
        "Componentes com MF < 50 que levam ao Conselho de Classe Final.",
        "Regimento 2024, Art. 92",
        True,
    ),
    (
        "LIMITE_COMPONENTES_PROGRESSAO_PARCIAL",
        "3",
        "INTEIRO",
        "Componentes em reprovação admitidos na Progressão Parcial.",
        "Regimento 2024, Art. 93",
        True,
    ),
    (
        "ALERTA_CONSELHO_PERCENTUAL",
        "30",
        "INTEIRO",
        "Alerta à coordenação quando mais que este percentual da turma não tem rendimento satisfatório.",
        "Regimento 2024, Art. 64",
        True,
    ),
    (
        "RENDIMENTO_SATISFATORIO_MINIMO",
        "70",
        "INTEIRO",
        "Nota da etapa a partir da qual o rendimento é satisfatório.",
        "Regimento 2024, Art. 64 (sem número); PRC-05 (interpretação: MB ≥ 70, Art. 63)",
        False,
    ),
    (
        "ARREDONDAMENTO_MEDIA",
        "HALF_EVEN",
        "TEXTO",
        "Arredondamento usado só para conferir os valores do boletim (os do SUAP são os oficiais).",
        "PRC-01 (evidência do boletim do SUAP, não da norma)",
        False,
    ),
    (
        "MATRICULA_PADRAO",
        r"^\d{12}$",
        "TEXTO",
        "Formato da matrícula do estudante (a validação usa ACADEMICO_MATRICULA_REGEX do .env).",
        "PRC-09 (12 dígitos no boletim de exemplo)",
        False,
    ),
    (
        "FAIXAS_DESEMPENHO",
        "40;70;86",
        "TEXTO",
        "Limites das faixas crítica [0,40), mediana [40,70), boa [70,86) e excelente [86,100] (critério exploratório).",
        "PRC-06 (só 40 e 70 têm âncora normativa)",
        False,
    ),
]


def criar(apps, schema_editor):
    ParametroRegra = apps.get_model("notas", "ParametroRegra")
    for chave, valor, tipo, descricao, fundamento, confirmada in PARAMETROS:
        ParametroRegra.objects.create(
            chave=chave,
            valor=valor,
            tipo=tipo,
            descricao=descricao,
            fundamento=fundamento,
            confirmada=confirmada,
            vigente_desde=DESDE,
        )


def remover(apps, schema_editor):
    ParametroRegra = apps.get_model("notas", "ParametroRegra")
    ParametroRegra.objects.filter(chave__in=[p[0] for p in PARAMETROS], vigente_desde=DESDE).delete()


class Migration(migrations.Migration):
    dependencies = [("notas", "0002_gatilhos_versao_imutavel")]

    operations = [migrations.RunPython(criar, remover)]
