"""Indicadores calculados de cada versão, guardados para não recalcular a cada visita (ID 7)."""

from django.db import models


class SnapshotIndicadores(models.Model):
    """Resultado de ``indicadores.calcular`` para uma versão, com a assinatura das regras usadas.

    Uma assinatura nova (outro limiar, outra confirmação, outro aluno fora das comparações ou outra
    versão do cálculo) gera outro snapshot; os antigos ficam como histórico do que foi mostrado.
    """

    importacao = models.ForeignKey(
        "importacao.Importacao", on_delete=models.CASCADE, related_name="snapshots_de_indicadores"
    )
    assinatura = models.CharField("assinatura das regras e das exclusões", max_length=80)
    calculado_em = models.DateTimeField("calculado em", auto_now_add=True)
    dados = models.JSONField("indicadores")

    class Meta:
        verbose_name = "snapshot de indicadores"
        verbose_name_plural = "snapshots de indicadores"
        constraints = [
            models.UniqueConstraint(fields=["importacao", "assinatura"], name="snapshot_unico_por_assinatura")
        ]

    def __str__(self):
        return f"Indicadores da importação {self.importacao_id} ({self.assinatura})"
