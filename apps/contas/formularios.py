"""Formulários de acesso (login e senhas) e do cadastro de usuários."""

from django import forms
from django.conf import settings
from django.contrib.auth import forms as auth_forms

from apps.contas.models import Perfil, Usuario
from apps.contas.validadores import dominios_permitidos
from apps.paineis.formularios import FormularioAcessivel


def _dominios_legiveis() -> str:
    return " ou ".join(f"@{d}" for d in dominios_permitidos())


class FormularioEntrar(FormularioAcessivel, auth_forms.AuthenticationForm):
    username = forms.EmailField(
        label="E-mail institucional",
        widget=forms.EmailInput(attrs={"autocomplete": "username", "autofocus": True, "spellcheck": "false"}),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages = {
            **self.error_messages,
            "invalid_login": (
                f"E-mail ou senha incorretos. Depois de {settings.AXES_FAILURE_LIMIT} tentativas erradas "
                "seguidas, a conta fica bloqueada por um tempo."
            ),
        }


class FormularioAlterarSenha(FormularioAcessivel, auth_forms.PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.pop("autofocus", None)
        self.fields["old_password"].label = "Senha atual"


class FormularioDefinirSenha(FormularioAcessivel, auth_forms.SetPasswordForm):
    pass


class FormularioEsqueciSenha(FormularioAcessivel, auth_forms.PasswordResetForm):
    email = forms.EmailField(
        label="E-mail institucional",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True, "spellcheck": "false"}),
    )


class FormularioUsuario(FormularioAcessivel, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["nome", "email", "perfil"]
        widgets = {
            "nome": forms.TextInput(attrs={"autocomplete": "off"}),
            "email": forms.EmailInput(attrs={"autocomplete": "off", "spellcheck": "false"}),
        }
        help_texts = {
            "perfil": (
                "Professor vê só os próprios diários; Coordenador, os diários do curso; "
                "Administrador gerencia os usuários e tudo o mais."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A ajuda do e-mail depende da configuração, então é definida aqui (depois do mixin).
        self.fields["email"].help_text = f"Precisa ser institucional ({_dominios_legiveis()})."
        id_email = self.auto_id % self.add_prefix("email")
        self.fields["email"].widget.attrs["aria-describedby"] = f"{id_email}_ajuda"


class FiltroUsuarios(forms.Form):
    SITUACOES = [
        ("", "Todas"),
        ("ativos", "Ativos"),
        ("desativados", "Desativados"),
        ("convite", "Convite pendente"),
    ]

    q = forms.CharField(label="Buscar por nome ou e-mail", required=False, widget=forms.SearchInput())
    perfil = forms.ChoiceField(label="Perfil", required=False, choices=[("", "Todos"), *Perfil.choices])
    situacao = forms.ChoiceField(label="Situação", required=False, choices=SITUACOES)
