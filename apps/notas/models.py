"""Notas e frequência de cada versão (IDs 6, 19 e 23) e parâmetros das regras (ParametroRegra).

As linhas de notas pertencem a uma importação (versão) e nunca são alteradas: uma correção chega como
uma nova versão. Os valores são os do boletim, que são os oficiais (PRC-01); "-" no boletim vira
NULL (ausente, não zero).
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

NOTA = {
    "max_digits": 5,
    "decimal_places": 2,
    "null": True,
    "blank": True,
    "validators": [MinValueValidator(Decimal(0)), MaxValueValidator(Decimal(100))],
}


class NotaImutavelError(Exception):
    """Tentativa de alterar uma linha de notas (correções chegam como nova versão)."""


def _entre_0_e_100(campo: str, nome: str) -> models.CheckConstraint:
    return models.CheckConstraint(
        condition=Q(**{f"{campo}__isnull": True}) | Q(**{f"{campo}__gte": 0, f"{campo}__lte": 100}), name=nome
    )


class LinhaImutavel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise NotaImutavelError("Notas de uma versão não são alteradas: importe uma nova versão.")
        super().save(*args, **kwargs)


class ResultadoAluno(LinhaImutavel):
    """A linha do aluno no boletim de uma versão: situação, faltas, frequência e médias."""

    importacao = models.ForeignKey(
        "importacao.Importacao", on_delete=models.PROTECT, related_name="resultados"
    )
    matricula = models.ForeignKey(
        "academico.MatriculaDiario", on_delete=models.PROTECT, related_name="resultados"
    )
    ordem = models.PositiveSmallIntegerField("nº no boletim")
    nome_no_boletim = models.CharField("nome no boletim", max_length=255)
    situacao = models.CharField("situação no SUAP", max_length=40)
    total_faltas = models.PositiveSmallIntegerField("total de faltas")
    frequencia_percentual = models.DecimalField("% de frequência", **NOTA)
    media_disciplina = models.DecimalField("média da disciplina (MD)", **NOTA)
    nota_avaliacao_final = models.DecimalField("nota da avaliação final (NAF)", **NOTA)
    faltas_avaliacao_final = models.PositiveSmallIntegerField("faltas na avaliação final", default=0)
    media_final = models.DecimalField("média final (MFD)", **NOTA)
    conceito = models.CharField(
        "conceito", max_length=20, blank=True, help_text="Quando o SUAP mostra conceito."
    )

    class Meta:
        verbose_name = "resultado do aluno na versão"
        verbose_name_plural = "resultados dos alunos nas versões"
        ordering = ["ordem"]
        constraints = [
            models.UniqueConstraint(fields=["importacao", "matricula"], name="aluno_uma_vez_por_versao"),
            _entre_0_e_100("frequencia_percentual", "frequencia_0_a_100"),
            _entre_0_e_100("media_disciplina", "md_0_a_100"),
            _entre_0_e_100("nota_avaliacao_final", "naf_0_a_100"),
            _entre_0_e_100("media_final", "mfd_0_a_100"),
        ]

    def __str__(self):
        return f"{self.nome_no_boletim} na {self.importacao}"

    @property
    def cancelado(self) -> bool:
        return self.situacao.strip().lower() == "cancelado"


class RegistroBimestral(LinhaImutavel):
    """Nota e faltas de uma etapa (bimestre) numa versão. Nota já é a registrada pelo SUAP (Art. 63 §1)."""

    resultado = models.ForeignKey(ResultadoAluno, on_delete=models.PROTECT, related_name="bimestres")
    bimestre = models.PositiveSmallIntegerField(
        "bimestre", validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    nota = models.DecimalField("nota da etapa", **NOTA)
    faltas = models.PositiveSmallIntegerField("faltas na etapa", default=0)

    class Meta:
        verbose_name = "registro bimestral"
        verbose_name_plural = "registros bimestrais"
        ordering = ["bimestre"]
        constraints = [
            models.UniqueConstraint(fields=["resultado", "bimestre"], name="bimestre_uma_vez_por_resultado"),
            models.CheckConstraint(condition=Q(bimestre__gte=1, bimestre__lte=4), name="bimestre_1_a_4"),
            _entre_0_e_100("nota", "nota_0_a_100"),
        ]
        indexes = [models.Index(fields=["bimestre"], name="registro_bimestre_idx")]

    def __str__(self):
        return f"{self.bimestre}º bimestre: {self.nota if self.nota is not None else '-'}"


class TipoParametro(models.TextChoices):
    INTEIRO = "INTEIRO", "Número inteiro"
    DECIMAL = "DECIMAL", "Número decimal"
    TEXTO = "TEXTO", "Texto"


class ParametroRegra(models.Model):
    """Limiar ou opção usada pelas regras do Regimento (E4). Mudar um valor = nova linha com nova vigência.

    `confirmada=False` marca valores que vêm de interpretação ou de pendência (PRC) e ainda precisam de
    validação institucional; a interface mostra o selo "pendente de confirmação".
    """

    chave = models.CharField("chave", max_length=60)
    valor = models.CharField("valor", max_length=200)
    tipo = models.CharField("tipo", max_length=10, choices=TipoParametro.choices)
    descricao = models.TextField("descrição")
    fundamento = models.CharField(
        "fundamento", max_length=255, help_text="Artigo do Regimento ou pendência (PRC)."
    )
    confirmada = models.BooleanField("confirmada institucionalmente", default=False)
    vigente_desde = models.DateField("vigente desde", default=timezone.localdate)

    class Meta:
        verbose_name = "parâmetro de regra"
        verbose_name_plural = "parâmetros de regras"
        ordering = ["chave", "-vigente_desde"]
        constraints = [
            models.UniqueConstraint(fields=["chave", "vigente_desde"], name="parametro_uma_vez_por_data")
        ]

    def __str__(self):
        return f"{self.chave} = {self.valor}"

    @property
    def valor_convertido(self):
        if self.tipo == TipoParametro.INTEIRO:
            return int(self.valor)
        if self.tipo == TipoParametro.DECIMAL:
            return Decimal(self.valor)
        return self.valor

    @classmethod
    def vigente(cls, chave: str, em=None) -> "ParametroRegra":
        """O parâmetro valendo na data `em` (padrão: hoje)."""
        data = em or timezone.localdate()
        return cls.objects.filter(chave=chave, vigente_desde__lte=data).latest("vigente_desde")
