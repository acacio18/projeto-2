from django.urls import path

from apps.contas import views

app_name = "contas"

urlpatterns = [
    path("entrar/", views.EntrarView.as_view(), name="entrar"),
    path("sair/", views.SairView.as_view(), name="sair"),
    path("senha/alterar/", views.AlterarSenhaView.as_view(), name="alterar_senha"),
    path("senha/esqueci/", views.EsqueciSenhaView.as_view(), name="esqueci_senha"),
    path("senha/esqueci/enviado/", views.EsqueciSenhaEnviadoView.as_view(), name="esqueci_senha_enviado"),
    path("senha/definir/<uidb64>/<token>/", views.DefinirSenhaView.as_view(), name="definir_senha"),
    path("senha/definida/", views.SenhaDefinidaView.as_view(), name="senha_definida"),
]
