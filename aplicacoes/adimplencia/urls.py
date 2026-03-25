from django.urls import path

from aplicacoes.adimplencia import views

app_name = 'adimplencia'

urlpatterns = [
    path('', views.lista_adimplencia, name='lista_adimplencia'),
    path('novo/', views.criar_adimplencia, name='criar_adimplencia'),
    path('<uuid:pk>/editar/', views.editar_adimplencia, name='editar_adimplencia'),
]
