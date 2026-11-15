"""Confirma os parâmetros que dependiam de interpretação (decisões do usuário em 11/11 e 14/11/2026).

O usuário decidiu que, nas questões de interpretação do Regimento, vale a leitura mais favorável e
lógica do próprio texto, sem esperar validação institucional. Ficam confirmados:
- MA = 40 com direito à AF, desde que a nota mínima do Anexo 01 seja alcançável (PRC-02);
- rendimento satisfatório = nota da etapa ≥ 70 (PRC-05);
- o sistema não arredonda: o valor do boletim é o oficial e o recálculo só confere (PRC-01);
- matrícula com 12 dígitos (PRC-09);
- faixas de desempenho 40, 70 e 86 (PRC-06).
"""

from django.db import migrations

DECISAO = "confirmada pelo usuário em {data}"
CONFIRMACOES = {
    "MEDIA_MINIMA_AVALIACAO_FINAL": "Regimento 2024, Art. 89 e Anexo 01; PRC-02: MA = 40 tem AF (mínima 65), "
    "leitura mais favorável do Regimento, " + DECISAO.format(data="14/11/2026"),
    "RENDIMENTO_SATISFATORIO_MINIMO": "Regimento 2024, Arts. 63 e 64; PRC-05: nota da etapa ≥ 70, "
    + DECISAO.format(data="14/11/2026"),
    "ARREDONDAMENTO_MEDIA": "PRC-01: o Regimento não define arredondamento; o sistema não arredonda e só confere "
    "o boletim, " + DECISAO.format(data="14/11/2026"),
    "MATRICULA_PADRAO": "PRC-09: matrícula com 12 dígitos, " + DECISAO.format(data="14/11/2026"),
    "FAIXAS_DESEMPENHO": "PRC-06: faixas [0,40), [40,70), [70,86) e [86,100], " + DECISAO.format(data="14/11/2026"),
}


def confirmar(apps, schema_editor):
    ParametroRegra = apps.get_model("notas", "ParametroRegra")
    for chave, fundamento in CONFIRMACOES.items():
        ParametroRegra.objects.filter(chave=chave).update(confirmada=True, fundamento=fundamento[:255])


def desfazer(apps, schema_editor):
    ParametroRegra = apps.get_model("notas", "ParametroRegra")
    ParametroRegra.objects.filter(chave__in=CONFIRMACOES).update(confirmada=False)


class Migration(migrations.Migration):
    dependencies = [("notas", "0003_parametros_do_regimento")]

    operations = [migrations.RunPython(confirmar, desfazer)]
