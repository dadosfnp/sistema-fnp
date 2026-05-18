"""URLs do Dicionário institucional."""

from django.urls import path

from aplicacoes.dicionario import views

app_name = 'dicionario'

urlpatterns = [
    path('', views.lista_dicionario, name='lista_dicionario'),
]
