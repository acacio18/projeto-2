from django.urls import path

from apps.academico import views_diarios as views

app_name = "diarios"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.novo, name="novo"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    path("<int:pk>/versoes/<int:importacao_pk>/confirmar/", views.confirmar_versao, name="confirmar"),
    path("<int:pk>/versoes/<int:importacao_pk>/descartar/", views.descartar_versao, name="descartar"),
    path("<int:pk>/versoes/<int:importacao_pk>/tornar-vigente/", views.tornar_vigente, name="tornar_vigente"),
]
