from django.urls import path

from aplicacoes.engajamento import views

app_name = 'engajamento'

urlpatterns = [
    path('', views.lista_engajamento, name='lista_engajamento'),
]
