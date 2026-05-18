"""URLs de Projetos institucionais."""

from django.urls import path

from aplicacoes.projetos import views

app_name = 'projetos'

urlpatterns = [
    path('', views.lista_projetos, name='lista_projetos'),
    path('novo/', views.criar_projeto, name='criar_projeto'),
    path('<uuid:pk>/', views.detalhe_projeto, name='detalhe_projeto'),
    path('<uuid:pk>/editar/', views.editar_projeto, name='editar_projeto'),
]
