"""URLs de Documentos — listagem, upload e remoção genéricos por entidade."""

from django.urls import path

from aplicacoes.documentos import views

app_name = 'documentos'

urlpatterns = [
    path(
        'de/<str:app_label>/<str:model_name>/<uuid:object_id>/',
        views.documentos_da_entidade,
        name='listar',
    ),
    path(
        'novo/<str:app_label>/<str:model_name>/<uuid:object_id>/',
        views.adicionar_documento,
        name='adicionar_documento',
    ),
    path('<uuid:pk>/remover/', views.remover_documento, name='remover_documento'),
]
