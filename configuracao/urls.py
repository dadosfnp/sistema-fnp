"""Configuracao de URLs raiz do Sistema FNP."""

from django.conf import settings
from django.conf.urls.static import static
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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
