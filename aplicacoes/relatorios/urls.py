from django.urls import path

from aplicacoes.relatorios import views

app_name = 'relatorios'

urlpatterns = [
    path('', views.painel, name='painel'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
]
