from django.urls import path

from aplicacoes.eventos import views

app_name = 'eventos'

urlpatterns = [
    path('', views.lista_eventos, name='lista_eventos'),
    path('<uuid:pk>/', views.detalhe_evento, name='detalhe_evento'),
]
