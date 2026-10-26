"""Rotas principais do SUAP V2."""

from django.urls import path

from apps.ops.views import healthz

urlpatterns = [
    path("healthz", healthz, name="healthz"),
]
