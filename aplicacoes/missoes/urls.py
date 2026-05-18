"""URLs de Missões institucionais."""

from django.urls import path

from aplicacoes.missoes import views

app_name = 'missoes'

urlpatterns = [
    path('', views.lista_missoes, name='lista_missoes'),
    path('novo/', views.criar_missao, name='criar_missao'),
    path('<uuid:pk>/', views.detalhe_missao, name='detalhe_missao'),
    path('<uuid:pk>/editar/', views.editar_missao, name='editar_missao'),
]
