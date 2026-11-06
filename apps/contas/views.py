"""Telas de acesso: entrar, sair, alterar senha, esqueci a senha e definir senha (convite)."""

from axes.utils import reset as zerar_tentativas
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from apps.auditoria.models import TipoEvento
from apps.auditoria.registro import registrar
from apps.contas import formularios


class EntrarView(auth_views.LoginView):
    template_name = "contas/entrar.html"
    form_class = formularios.FormularioEntrar
    redirect_authenticated_user = True


class SairView(auth_views.LogoutView):
    """Só aceita POST (o botão "Sair" envia um formulário com token CSRF)."""

    def post(self, request, *args, **kwargs):
        resposta = super().post(request, *args, **kwargs)
        messages.info(request, "Você saiu do SUAP V2.")
        return resposta


class AlterarSenhaView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = "contas/alterar_senha.html"
    form_class = formularios.FormularioAlterarSenha
    success_url = reverse_lazy("painel")

    def form_valid(self, form):
        resposta = super().form_valid(form)  # mantém a sessão atual e encerra as outras
        registrar(TipoEvento.SENHA_ALTERADA, request=self.request, usuario=self.request.user)
        messages.success(self.request, "Senha alterada.")
        return resposta


class EsqueciSenhaView(auth_views.PasswordResetView):
    """Responde igual para e-mail cadastrado ou não (não revela quem tem conta)."""

    template_name = "contas/esqueci_senha.html"
    form_class = formularios.FormularioEsqueciSenha
    email_template_name = "contas/emails/redefinicao.txt"
    subject_template_name = "contas/emails/redefinicao_assunto.txt"
    success_url = reverse_lazy("contas:esqueci_senha_enviado")

    def form_valid(self, form):
        registrar(
            TipoEvento.SENHA_REDEFINICAO_PEDIDA,
            request=self.request,
            email_informado=form.cleaned_data["email"],
        )
        return super().form_valid(form)


class EsqueciSenhaEnviadoView(auth_views.PasswordResetDoneView):
    template_name = "contas/esqueci_senha_enviado.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "validade_horas": settings.PASSWORD_RESET_TIMEOUT // 3600,
        }


class DefinirSenhaView(auth_views.PasswordResetConfirmView):
    """Usada pelo convite e pela redefinição. O link vale uma vez só."""

    template_name = "contas/definir_senha.html"
    form_class = formularios.FormularioDefinirSenha
    success_url = reverse_lazy("contas:senha_definida")

    def form_valid(self, form):
        resposta = super().form_valid(form)
        zerar_tentativas(username=form.user.email)  # quem redefiniu a senha não fica bloqueado
        registrar(TipoEvento.SENHA_DEFINIDA, request=self.request, usuario=form.user, objeto=form.user)
        return resposta


class SenhaDefinidaView(auth_views.PasswordResetCompleteView):
    template_name = "contas/senha_definida.html"
