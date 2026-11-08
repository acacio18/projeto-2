from django.urls import path

from apps.academico import views_cadastros as views

app_name = "cadastros"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("cursos/", views.cursos, name="cursos"),
    path("cursos/novo/", views.curso_novo, name="curso_novo"),
    path("cursos/<int:pk>/", views.curso_detalhe, name="curso"),
    path("cursos/<int:pk>/editar/", views.curso_editar, name="curso_editar"),
    path("cursos/<int:pk>/excluir/", views.curso_excluir, name="curso_excluir"),
    path("cursos/<int:pk>/coordenadores/", views.coordenador_vincular, name="coordenador_vincular"),
    path(
        "cursos/<int:pk>/coordenadores/<int:usuario_pk>/remover/",
        views.coordenador_desvincular,
        name="coordenador_desvincular",
    ),
    path("turmas/", views.lista, {"tipo": "turmas"}, name="turmas"),
    path("turmas/nova/", views.novo, {"tipo": "turmas"}, name="turma_nova"),
    path("turmas/<int:pk>/", views.editar, {"tipo": "turmas"}, name="turma_editar"),
    path("turmas/<int:pk>/excluir/", views.excluir, {"tipo": "turmas"}, name="turma_excluir"),
    path("disciplinas/", views.lista, {"tipo": "disciplinas"}, name="disciplinas"),
    path("disciplinas/nova/", views.novo, {"tipo": "disciplinas"}, name="disciplina_nova"),
    path("disciplinas/<int:pk>/", views.editar, {"tipo": "disciplinas"}, name="disciplina_editar"),
    path("disciplinas/<int:pk>/excluir/", views.excluir, {"tipo": "disciplinas"}, name="disciplina_excluir"),
]
