"""URLs de Comunicação — composição e histórico de mala direta."""

from django.urls import path

from aplicacoes.comunicacao import views

app_name = 'comunicacao'

urlpatterns = [
    path(
        'enviar/<str:app_label>/<str:model_name>/<uuid:object_id>/',
        views.compor_envio,
        name='compor_envio',
    ),
    path(
        'modal/<str:app_label>/<str:model_name>/<uuid:object_id>/',
        views.compor_envio_modal,
        name='compor_envio_modal',
    ),
    path(
        'processar/<str:app_label>/<str:model_name>/<uuid:object_id>/',
        views.processar_envio,
        name='processar_envio',
    ),
    path(
        'historico/<str:app_label>/<str:model_name>/<uuid:object_id>/',
        views.historico_envios,
        name='historico_envios',
    ),
]
