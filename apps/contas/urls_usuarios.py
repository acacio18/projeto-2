from django.urls import path

from apps.contas import views_usuarios as views

app_name = "usuarios"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.novo, name="novo"),
    path("<int:pk>/", views.editar, name="editar"),
    path("<int:pk>/desativar/", views.desativar, name="desativar"),
    path("<int:pk>/reativar/", views.reativar, name="reativar"),
    path("<int:pk>/reenviar-convite/", views.reenviar_convite, name="reenviar_convite"),
    path("<int:pk>/desbloquear/", views.desbloquear, name="desbloquear"),
]
