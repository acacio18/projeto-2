"""Formulários dos cadastros acadêmicos. As opções de curso, turma e professor já vêm limitadas ao escopo."""

from django import forms

from apps.academico.models import Curso, Diario, Disciplina, Turma
from apps.contas import escopo
from apps.paineis.formularios import FormularioAcessivel


class FormularioCurso(FormularioAcessivel, forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["codigo", "nome"]
        help_texts = {"codigo": "Número do curso no SUAP, como aparece no boletim (por exemplo, 661)."}


class _ComCursoDoEscopo(FormularioAcessivel, forms.ModelForm):
    """O campo "curso" só oferece os cursos que o usuário pode gerenciar."""

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curso"].queryset = escopo.cursos_gerenciaveis(usuario).order_by("nome")
        self.fields["curso"].empty_label = "Escolha o curso"


class FormularioTurma(_ComCursoDoEscopo):
    class Meta:
        model = Turma
        fields = ["curso", "ano_letivo", "serie", "identificador"]


class FormularioDisciplina(_ComCursoDoEscopo):
    class Meta:
        model = Disciplina
        fields = ["curso", "codigo", "nome", "carga_horaria_horas", "optativa"]


class FormularioDiario(_ComCursoDoEscopo):
    class Meta:
        model = Diario
        fields = [
            "codigo",
            "curso",
            "disciplina",
            "ano_letivo",
            "periodo_letivo",
            "turma",
            "professor",
            "aulas_previstas",
            "carga_horaria_horas",
        ]
        help_texts = {
            "codigo": "Número do diário no SUAP (no boletim: “Diário: 70764 - …”).",
            "disciplina": "Precisa ser do mesmo curso do diário.",
        }

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, usuario=usuario, **kwargs)
        cursos = escopo.cursos_gerenciaveis(usuario)
        self.fields["disciplina"].queryset = (
            Disciplina.objects.filter(curso__in=cursos)
            .select_related("curso")
            .order_by("curso__nome", "nome")
        )
        self.fields["disciplina"].label_from_instance = lambda d: f"{d.codigo} - {d.nome} ({d.curso.nome})"
        self.fields["turma"].queryset = (
            Turma.objects.filter(curso__in=cursos)
            .select_related("curso")
            .order_by("-ano_letivo", "identificador")
        )
        self.fields["turma"].label_from_instance = lambda t: (
            f"{t.identificador} ({t.ano_letivo}, {t.curso.nome})"
        )
        self.fields["turma"].empty_label = "Sem turma por enquanto"
        self.fields["professor"].queryset = escopo.professores_atribuiveis()
        self.fields["professor"].label_from_instance = lambda u: f"{u.nome} ({u.email})"
        self.fields["professor"].empty_label = "Sem professor por enquanto"


class FormularioCoordenador(FormularioAcessivel, forms.Form):
    usuario = forms.ModelChoiceField(
        label="Coordenador", queryset=None, empty_label="Escolha um usuário com perfil Coordenador"
    )

    def __init__(self, *args, curso, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["usuario"].queryset = escopo.coordenadores_disponiveis().exclude(
            coordenacoes__curso=curso
        )
        self.fields["usuario"].label_from_instance = lambda u: f"{u.nome} ({u.email})"


class FiltroDiarios(forms.Form):
    SITUACOES = [
        ("", "Todas"),
        ("com_notas", "Com notas vigentes"),
        ("aguardando", "Aguardando confirmação"),
        ("sem_notas", "Sem notas"),
        ("sem_turma", "Sem turma"),
    ]

    q = forms.CharField(label="Buscar por código ou disciplina", required=False, widget=forms.SearchInput())
    ano = forms.IntegerField(label="Ano letivo", required=False, min_value=2000, max_value=2100)
    situacao = forms.ChoiceField(label="Situação", required=False, choices=SITUACOES)


class FiltroCadastros(forms.Form):
    q = forms.CharField(label="Buscar", required=False, widget=forms.SearchInput())
    curso = forms.ModelChoiceField(label="Curso", required=False, queryset=None, empty_label="Todos")

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curso"].queryset = escopo.cursos_visiveis(usuario).order_by("nome")
