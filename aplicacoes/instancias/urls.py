"""URLs de Instâncias — interface dedicada a Espaços de Diálogo Federativo."""

from django.urls import path

from aplicacoes.instancias import views

app_name = 'instancias'

urlpatterns = [
    path('', views.lista_instancias, name='lista_instancias'),
    path('novo/', views.criar_instancia, name='criar_instancia'),
    path('<uuid:pk>/', views.detalhe_instancia, name='detalhe_instancia'),
    path('<uuid:pk>/editar/', views.editar_instancia, name='editar_instancia'),
]
