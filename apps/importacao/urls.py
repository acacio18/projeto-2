from django.urls import path

from apps.importacao import views

app_name = "importacoes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("enviar/", views.enviar, name="enviar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/situacao/", views.situacao, name="situacao"),
    path("<int:pk>/ler-de-novo/", views.ler_de_novo, name="ler_de_novo"),
    path("lotes/<int:pk>/", views.lote, name="lote"),
    path("lotes/<int:pk>/situacao/", views.lote_situacao, name="lote_situacao"),
]
