"""Configuração de URLs raiz do Sistema FNP."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('aplicacoes.nucleo.urls')),
    path('cadastro/', include('aplicacoes.cadastro.urls')),
    path('adimplencia/', include('aplicacoes.adimplencia.urls')),
    path('engajamento/', include('aplicacoes.engajamento.urls')),
    path('eventos/', include('aplicacoes.eventos.urls')),
    path('relatorios/', include('aplicacoes.relatorios.urls')),
]
