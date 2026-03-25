from django.urls import path

from aplicacoes.adimplencia import views

app_name = 'adimplencia'

urlpatterns = [
    path('', views.lista_adimplencia, name='lista_adimplencia'),
]
