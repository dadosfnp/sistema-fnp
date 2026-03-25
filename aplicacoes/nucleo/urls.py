from django.urls import path

from aplicacoes.nucleo import views

app_name = 'nucleo'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('entrar/', views.entrar, name='entrar'),
    path('sair/', views.sair, name='sair'),
]
