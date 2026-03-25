from django.urls import path

from aplicacoes.relatorios import views

app_name = 'relatorios'

urlpatterns = [
    path('', views.painel, name='painel'),
]
