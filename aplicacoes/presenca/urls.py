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
    path('recepcao/<uuid:pk>/saida/', views.recepcao_registrar_saida, name='recepcao_registrar_saida'),
    path('recepcao/historico/', views.recepcao_historico, name='recepcao_historico'),
    # Pre-credenciamento
    path('credenciamento/', views.credenciamento_lista, name='credenciamento_lista'),
    path('credenciamento/novo/', views.credenciamento_novo, name='credenciamento_novo'),
    path('credenciamento/<uuid:pk>/confirmar/', views.credenciamento_confirmar_visita, name='credenciamento_confirmar_visita'),
    path('pre/<str:token>/', views.pre_credenciamento_publico, name='pre_credenciamento_publico'),
]
