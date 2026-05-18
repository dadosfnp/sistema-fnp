from django.urls import path

from aplicacoes.relatorios import views

app_name = 'relatorios'

urlpatterns = [
    path('', views.painel, name='painel'),
    path('mapa/', views.mapa, name='mapa'),
    path('mapa/dados/', views.mapa_dados, name='mapa_dados'),
    path('mapa/dados-uf/', views.mapa_dados_uf, name='mapa_dados_uf'),
    path('comparar/municipios/', views.comparar_municipios, name='comparar_municipios'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
]
