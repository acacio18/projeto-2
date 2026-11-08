"""Cadastros acadêmicos (IDs 6, 16 e 17): cursos, turmas, disciplinas, diários e estudantes.

Os códigos são os do SUAP (curso "661", disciplina "TIN.0054", diário "70764") e servem para evitar
duplicatas quando o mesmo boletim, ou outro do mesmo diário, é importado de novo.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

from apps.contas.models import Perfil

ANO_MINIMO, ANO_MAXIMO = 2000, 2100


class Registro(models.Model):
    """Base com datas de criação e de alteração."""

    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


class Curso(Registro):
    codigo = models.CharField("código no SUAP", max_length=20, unique=True)
    nome = models.CharField("nome", max_length=255)
    coordenadores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="CoordenacaoCurso",
        related_name="cursos_coordenados",
        blank=True,
        verbose_name="coordenadores",
    )

    class Meta:
        verbose_name = "curso"
        verbose_name_plural = "cursos"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class CoordenacaoCurso(models.Model):
    """Vínculo coordenador ↔ curso, mantido pelo Administrador (PRC-16: muitos-para-muitos)."""

    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="coordenacoes")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="coordenacoes",
        verbose_name="coordenador",
    )
    desde = models.DateTimeField("desde", auto_now_add=True)

    class Meta:
        verbose_name = "coordenação de curso"
        verbose_name_plural = "coordenações de curso"
        constraints = [models.UniqueConstraint(fields=["curso", "usuario"], name="coordenacao_unica")]

    def __str__(self):
        return f"{self.usuario.nome} coordena {self.curso.nome}"

    def clean(self):
        if self.usuario_id and self.usuario.perfil != Perfil.COORDENADOR:
            raise ValidationError({"usuario": "Só usuários com perfil Coordenador podem coordenar um curso."})


class Turma(Registro):
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="turmas")
    ano_letivo = models.PositiveSmallIntegerField(
        "ano letivo", validators=[MinValueValidator(ANO_MINIMO), MaxValueValidator(ANO_MAXIMO)]
    )
    serie = models.PositiveSmallIntegerField(
        "série (ano do curso)",
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="1º a 4º ano do curso integrado.",
    )
    identificador = models.CharField(
        "identificação",
        max_length=50,
        help_text="Como a turma é conhecida no campus, por exemplo “3º A” ou “TIN 3A”.",
    )

    class Meta:
        verbose_name = "turma"
        verbose_name_plural = "turmas"
        ordering = ["-ano_letivo", "curso__nome", "identificador"]
        constraints = [
            models.UniqueConstraint(
                fields=["curso", "ano_letivo", "identificador"], name="turma_unica_no_ano"
            ),
            models.CheckConstraint(
                condition=Q(ano_letivo__gte=ANO_MINIMO, ano_letivo__lte=ANO_MAXIMO), name="turma_ano_valido"
            ),
            models.CheckConstraint(
                condition=Q(serie__isnull=True) | Q(serie__gte=1, serie__lte=4), name="turma_serie_1_a_4"
            ),
        ]
        indexes = [models.Index(fields=["curso", "ano_letivo"], name="turma_curso_ano_idx")]

    def __str__(self):
        return f"{self.identificador} ({self.ano_letivo})"


class Disciplina(Registro):
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="disciplinas")
    codigo = models.CharField("código no SUAP", max_length=30, help_text="Por exemplo, “TIN.0054”.")
    nome = models.CharField("nome", max_length=255)
    carga_horaria_horas = models.PositiveSmallIntegerField("carga horária (horas)", null=True, blank=True)
    optativa = models.BooleanField(
        "optativa",
        default=False,
        help_text="Língua estrangeira optativa: a reprovação não retém na série (Regimento, Art. 68).",
    )

    class Meta:
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(fields=["curso", "codigo"], name="disciplina_codigo_unico_no_curso")
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Diario(Registro):
    """Um componente curricular de uma turma num período letivo, com o professor responsável."""

    codigo = models.CharField(
        "código no SUAP", max_length=20, help_text="Número do diário, por exemplo “70764”."
    )
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="diarios")
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, related_name="diarios")
    turma = models.ForeignKey(
        Turma,
        on_delete=models.PROTECT,
        related_name="diarios",
        null=True,
        blank=True,
        help_text=(
            "O boletim do SUAP não informa a turma: ela é vinculada pela coordenação ou pela administração."
        ),
    )
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="diarios",
        null=True,
        blank=True,
        verbose_name="professor responsável",
    )
    ano_letivo = models.PositiveSmallIntegerField(
        "ano letivo", validators=[MinValueValidator(ANO_MINIMO), MaxValueValidator(ANO_MAXIMO)]
    )
    periodo_letivo = models.PositiveSmallIntegerField("período letivo", default=1)
    aulas_previstas = models.PositiveSmallIntegerField("aulas previstas", null=True, blank=True)
    carga_horaria_horas = models.PositiveSmallIntegerField("carga horária (horas)", null=True, blank=True)

    class Meta:
        verbose_name = "diário"
        verbose_name_plural = "diários"
        ordering = ["-ano_letivo", "disciplina__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["codigo", "ano_letivo", "periodo_letivo"], name="diario_unico_no_periodo"
            ),
            models.CheckConstraint(
                condition=Q(ano_letivo__gte=ANO_MINIMO, ano_letivo__lte=ANO_MAXIMO), name="diario_ano_valido"
            ),
        ]
        indexes = [
            models.Index(fields=["ano_letivo", "periodo_letivo"], name="diario_periodo_idx"),
            models.Index(fields=["curso", "ano_letivo"], name="diario_curso_ano_idx"),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.disciplina.nome} ({self.ano_letivo}/{self.periodo_letivo})"

    def clean(self):
        erros = {}
        if self.disciplina_id and self.curso_id and self.disciplina.curso_id != self.curso_id:
            erros["disciplina"] = "A disciplina precisa ser do mesmo curso do diário."
        if self.turma_id and self.curso_id and self.turma.curso_id != self.curso_id:
            erros["turma"] = "A turma precisa ser do mesmo curso do diário."
        if self.turma_id and self.turma.ano_letivo != self.ano_letivo:
            erros.setdefault("turma", "A turma precisa ser do mesmo ano letivo do diário.")
        if self.professor_id and (
            not self.professor.is_active
            or self.professor.perfil not in (Perfil.PROFESSOR, Perfil.COORDENADOR)
        ):
            erros["professor"] = "Escolha um professor ou coordenador ativo."
        if erros:
            raise ValidationError(erros)


def validar_matricula(valor: str) -> None:
    """Formato da matrícula (PRC-09: 12 dígitos no boletim de exemplo; configurável)."""
    RegexValidator(settings.ACADEMICO_MATRICULA_REGEX, "Matrícula fora do formato esperado.")(valor)


class Estudante(Registro):
    matricula = models.CharField("matrícula", max_length=20, unique=True, validators=[validar_matricula])
    nome = models.CharField("nome", max_length=255)

    class Meta:
        verbose_name = "estudante"
        verbose_name_plural = "estudantes"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.matricula})"


class MatriculaDiario(models.Model):
    """O estudante no diário. As notas e a situação de cada versão ficam em notas.ResultadoAluno."""

    estudante = models.ForeignKey(Estudante, on_delete=models.PROTECT, related_name="matriculas")
    diario = models.ForeignKey(Diario, on_delete=models.PROTECT, related_name="matriculas")
    excluir_das_comparacoes = models.BooleanField(
        "fora de rankings e comparações",
        default=False,
        help_text="Decisão do professor (Regimento, Art. 72). O motivo não é registrado.",
    )

    class Meta:
        verbose_name = "matrícula no diário"
        verbose_name_plural = "matrículas no diário"
        constraints = [
            models.UniqueConstraint(fields=["estudante", "diario"], name="matricula_unica_no_diario")
        ]

    def __str__(self):
        return f"{self.estudante} em {self.diario.codigo}"
