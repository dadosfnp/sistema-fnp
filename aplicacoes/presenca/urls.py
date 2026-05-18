"""URLs de Presença universal."""

from django.urls import path

from aplicacoes.presenca import views

app_name = 'presenca'

urlpatterns = [
    path(
        'marcar/<str:app_label>/<str:model_name>/<uuid:object_id>/',
        views.marcar_presencas,
        name='marcar_presencas',
    ),
    path(
        'adicionar-pessoa/<str:app_label>/<str:model_name>/<uuid:object_id>/',
        views.adicionar_pessoa_modal,
        name='adicionar_pessoa_modal',
    ),
]
