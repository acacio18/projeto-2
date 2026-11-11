"""Rotas principais do SUAP V2."""

from django.urls import include, path

from apps.ops.views import healthz
from apps.paineis import views as paineis

urlpatterns = [
    path("", paineis.inicio, name="inicio"),
    path("painel/", paineis.painel, name="painel"),
    path("", include("apps.contas.urls")),
    path("usuarios/", include("apps.contas.urls_usuarios")),
    path("diarios/", include("apps.academico.urls_diarios")),
    path("importacoes/", include("apps.importacao.urls")),
    path("cadastros/", include("apps.academico.urls_cadastros")),
    path("healthz", healthz, name="healthz"),
]
