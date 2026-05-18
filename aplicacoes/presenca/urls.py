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
]
