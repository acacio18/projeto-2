"""Formulário de envio de boletins (um ou vários PDFs, ou ZIPs com PDFs)."""

from django import forms
from django.conf import settings

from apps.paineis.formularios import FormularioAcessivel


class EntradaDeVariosArquivos(forms.FileInput):
    allow_multiple_selected = True


class CampoDeVariosArquivos(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", EntradaDeVariosArquivos(attrs={"accept": ".pdf,.zip,application/pdf"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        limpar = super().clean
        if isinstance(data, list | tuple):
            return [limpar(item, initial) for item in data]
        return [limpar(data, initial)]


class FormularioEnvio(FormularioAcessivel, forms.Form):
    arquivos = CampoDeVariosArquivos(label="Boletins do SUAP (PDF)")
    bimestre_corte = forms.TypedChoiceField(
        label="Até qual bimestre as notas estão fechadas?",
        choices=[(n, f"{n}º bimestre") for n in range(1, 5)],
        coerce=int,
        initial=4,
        help_text=(
            "O boletim do SUAP traz os quatro bimestres. As análises consideram só até o bimestre escolhido; "
            "notas posteriores ficam guardadas e são avisadas."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["arquivos"].help_text = (
            "Exporte no SUAP o “Boletim de Notas do Diário” em PDF. "
            "Pode enviar vários de uma vez, ou um ZIP, "
            f"até {settings.IMPORTACAO_LOTE_MAXIMO_ARQUIVOS} arquivos de no máximo "
            f"{settings.IMPORTACAO_TAMANHO_MAXIMO_MB} MB cada."
        )
        id_arquivos = self.auto_id % self.add_prefix("arquivos")
        self.fields["arquivos"].widget.attrs["aria-describedby"] = f"{id_arquivos}_ajuda"
