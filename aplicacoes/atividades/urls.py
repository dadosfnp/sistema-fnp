"""URLs de Atividades — reuniões e encontros de Instâncias."""

from django.urls import path

from aplicacoes.atividades import views

app_name = 'atividades'

urlpatterns = [
    path('', views.lista_atividades, name='lista_atividades'),
    path('novo/', views.criar_atividade, name='criar_atividade'),
    path('<uuid:pk>/', views.detalhe_atividade, name='detalhe_atividade'),
    path('<uuid:pk>/editar/', views.editar_atividade, name='editar_atividade'),
]
