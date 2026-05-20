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
    # Recepcao / check-in de visitantes
    path('recepcao/', views.recepcao, name='recepcao'),
    path('recepcao/novo/', views.recepcao_novo, name='recepcao_novo'),
    path('recepcao/buscar-pessoa/', views.recepcao_buscar_pessoa, name='recepcao_buscar_pessoa'),
    path('recepcao/<uuid:pk>/editar/', views.recepcao_editar, name='recepcao_editar'),
    path('recepcao/historico/', views.recepcao_historico, name='recepcao_historico'),
    # Pre-credenciamento
    path('credenciamento/', views.credenciamento_lista, name='credenciamento_lista'),
    path('credenciamento/novo/', views.credenciamento_novo, name='credenciamento_novo'),
    path('credenciamento/<uuid:pk>/confirmar/', views.credenciamento_confirmar_visita, name='credenciamento_confirmar_visita'),
    path('pre/<str:token>/', views.pre_credenciamento_publico, name='pre_credenciamento_publico'),
    # Modal de pre-credenciamento a partir de uma entidade
    path(
        'credenciamento/modal/<str:app_label>/<str:model_name>/<uuid:object_id>/',
        views.credenciamento_modal_entidade,
        name='credenciamento_modal_entidade',
    ),
    # Identificacao automatica via face-api.js
    path('identificar/', views.identificar_facial, name='identificar_facial'),
    path('identificar/buscar/', views.identificar_facial_buscar, name='identificar_facial_buscar'),
    path('identificar/manual/', views.identificar_facial_busca_manual, name='identificar_facial_busca_manual'),
    path('identificar/<uuid:pk>/embedding/', views.identificar_facial_atualizar_embedding, name='identificar_facial_atualizar_embedding'),
]
