"""Importação de um boletim = uma versão das notas de um diário (IDs 3, 6 e 19).

Cada boletim importado gera uma nova versão; nada é sobrescrito. A versão vigente de um diário é a
que o professor confirmou por último (ou a que um responsável escolheu de volta). Uma versão
confirmada nunca é alterada nem apagada: o modelo recusa e um gatilho no PostgreSQL também
(migração 0002).
"""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class VersaoImutavelError(Exception):
    """Tentativa de alterar ou apagar uma versão já confirmada."""


class StatusImportacao(models.TextChoices):
    RECEBIDA = "RECEBIDA", "Recebida"
    PROCESSANDO = "PROCESSANDO", "Lendo o boletim"
    AGUARDANDO_CONFIRMACAO = "AGUARDANDO_CONFIRMACAO", "Aguardando confirmação"
    CONFIRMADA = "CONFIRMADA", "Confirmada"
    DESCARTADA = "DESCARTADA", "Descartada"
    FALHOU = "FALHOU", "Falhou"


class MetodoExtracao(models.TextChoices):
    TEXTO = "TEXTO", "Texto do PDF"
    OCR = "OCR", "OCR (PDF digitalizado)"
    DEMONSTRACAO = "DEMONSTRACAO", "Dados de demonstração"


def caminho_do_arquivo(instancia, nome_original):
    # Nome aleatório: o nome original (que pode ter dado pessoal) fica só no banco.
    return f"boletins/{uuid.uuid4().hex}.pdf"


class LoteImportacao(models.Model):
    """Um envio de um ou mais boletins (vários PDFs ou um ZIP) — ID 18. Cada arquivo é independente."""

    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="lotes")
    criado_em = models.DateTimeField("enviado em", auto_now_add=True)
    bimestre_corte = models.PositiveSmallIntegerField("bimestre informado")
    ignorados = models.JSONField(
        "arquivos ignorados",
        default=list,
        blank=True,
        help_text="Arquivos do envio que não eram PDF válidos.",
    )

    class Meta:
        verbose_name = "lote de importação"
        verbose_name_plural = "lotes de importação"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Envio de {timezone.localtime(self.criado_em):%d/%m/%Y %H:%M}"


# Campos que não mudam depois da confirmação (só "vigente" pode mudar).
CAMPOS_CONGELADOS = [
    "diario_id",
    "numero_versao",
    "status",
    "bimestre_corte",
    "sha256",
    "arquivo",
    "aulas_ministradas",
    "cabecalho",
    "relatorio_validacao",
    "confirmada_por_id",
    "confirmada_em",
]


class Importacao(models.Model):
    lote = models.ForeignKey(
        LoteImportacao, on_delete=models.PROTECT, related_name="importacoes", null=True, blank=True
    )
    diario = models.ForeignKey(
        "academico.Diario", on_delete=models.PROTECT, related_name="importacoes", null=True, blank=True
    )
    numero_versao = models.PositiveIntegerField("versão", null=True, blank=True)
    vigente = models.BooleanField("vigente", default=False)
    status = models.CharField(
        "situação", max_length=30, choices=StatusImportacao.choices, default=StatusImportacao.RECEBIDA
    )
    bimestre_corte = models.PositiveSmallIntegerField(
        "bimestre informado", help_text="Último bimestre considerado fechado neste boletim (PRC-17)."
    )
    arquivo = models.FileField("arquivo PDF", upload_to=caminho_do_arquivo, blank=True)
    nome_arquivo_original = models.CharField("nome do arquivo enviado", max_length=255, blank=True)
    tamanho_bytes = models.PositiveIntegerField("tamanho (bytes)", default=0)
    sha256 = models.CharField("SHA-256", max_length=64, db_index=True)
    metodo_extracao = models.CharField(
        "como foi lido", max_length=20, choices=MetodoExtracao.choices, default=MetodoExtracao.TEXTO
    )
    versao_extrator = models.CharField("versão do leitor", max_length=20, blank=True)
    aulas_ministradas = models.PositiveSmallIntegerField("aulas ministradas", null=True, blank=True)
    cabecalho = models.JSONField("cabeçalho lido", default=dict, blank=True)
    relatorio_validacao = models.JSONField("relatório de validação", default=dict, blank=True)
    enviada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="importacoes_enviadas"
    )
    criada_em = models.DateTimeField("enviada em", auto_now_add=True)
    confirmada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="importacoes_confirmadas",
        null=True,
        blank=True,
    )
    confirmada_em = models.DateTimeField("confirmada em", null=True, blank=True)

    class Meta:
        verbose_name = "importação (versão)"
        verbose_name_plural = "importações (versões)"
        ordering = ["-criada_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["diario"], condition=Q(vigente=True), name="uma_versao_vigente_por_diario"
            ),
            models.UniqueConstraint(fields=["diario", "numero_versao"], name="numero_de_versao_unico"),
            models.CheckConstraint(
                condition=Q(bimestre_corte__gte=1, bimestre_corte__lte=4), name="corte_1_a_4"
            ),
            models.CheckConstraint(
                condition=Q(vigente=False) | Q(status=StatusImportacao.CONFIRMADA),
                name="vigente_so_se_confirmada",
            ),
            models.CheckConstraint(
                condition=~Q(status=StatusImportacao.CONFIRMADA)
                | Q(diario__isnull=False, numero_versao__isnull=False, confirmada_em__isnull=False),
                name="confirmada_tem_diario_versao_e_data",
            ),
        ]
        indexes = [models.Index(fields=["diario", "status"], name="importacao_diario_status_idx")]

    def __str__(self):
        if self.numero_versao:
            return f"Versão {self.numero_versao} do diário {self.diario.codigo}"
        return f"Importação {self.pk} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            original = Importacao.objects.filter(pk=self.pk).values(*CAMPOS_CONGELADOS).first()
            if original and original["status"] == StatusImportacao.CONFIRMADA:
                mudou = [c for c in CAMPOS_CONGELADOS if original[c] != getattr(self, c)]
                if mudou:
                    raise VersaoImutavelError(
                        f"Versão confirmada não pode ser alterada ({', '.join(mudou)})."
                    )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.confirmada:
            raise VersaoImutavelError("Versão confirmada não pode ser apagada.")
        return super().delete(*args, **kwargs)

    @property
    def confirmada(self) -> bool:
        return self.status == StatusImportacao.CONFIRMADA
