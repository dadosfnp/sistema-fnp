from django.urls import path

from aplicacoes.eventos import views

app_name = 'eventos'

urlpatterns = [
    path('', views.lista_eventos, name='lista_eventos'),
    path('novo/', views.criar_evento, name='criar_evento'),
    path('<uuid:pk>/', views.detalhe_evento, name='detalhe_evento'),
    path('<uuid:pk>/editar/', views.editar_evento, name='editar_evento'),
    path('participacao/novo/', views.criar_participacao, name='criar_participacao'),
    path('participacao/novo/<uuid:evento_pk>/', views.criar_participacao, name='criar_participacao_evento'),
    path('participacao/<uuid:pk>/editar/', views.editar_participacao, name='editar_participacao'),
]
