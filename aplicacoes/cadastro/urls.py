from django.urls import path

from aplicacoes.cadastro import views

app_name = 'cadastro'

urlpatterns = [
    path('pessoas/', views.lista_pessoas, name='lista_pessoas'),
    path('pessoas/novo/', views.criar_pessoa, name='criar_pessoa'),
    path('pessoas/<uuid:pk>/', views.detalhe_pessoa, name='detalhe_pessoa'),
    path('pessoas/<uuid:pk>/editar/', views.editar_pessoa, name='editar_pessoa'),
    path('municipios/', views.lista_municipios, name='lista_municipios'),
    path('municipios/novo/', views.criar_municipio, name='criar_municipio'),
    path('municipios/<uuid:pk>/', views.detalhe_municipio, name='detalhe_municipio'),
    path('municipios/<uuid:pk>/certidao.pdf', views.certidao_municipio, name='certidao_municipio'),
    path('municipios/<uuid:pk>/editar/', views.editar_municipio, name='editar_municipio'),
]
