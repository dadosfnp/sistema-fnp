"""Configuracao de URLs raiz do Sistema FNP."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

from aplicacoes.nucleo.api import EngajamentoViewSet, MunicipioViewSet, PessoaViewSet

api_router = routers.DefaultRouter()
api_router.register(r'municipios', MunicipioViewSet, basename='api-municipio')
api_router.register(r'pessoas', PessoaViewSet, basename='api-pessoa')
api_router.register(r'engajamentos', EngajamentoViewSet, basename='api-engajamento')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_router.urls)),
    path('api/v1/token/', obtain_auth_token, name='api-token'),
    path('portal/', __import__('aplicacoes.nucleo.views', fromlist=['portal_prefeito']).portal_prefeito, name='portal_prefeito'),
    path('', include('aplicacoes.nucleo.urls')),
    path('cadastro/', include('aplicacoes.cadastro.urls')),
    path('instancias/', include('aplicacoes.instancias.urls')),
    path('projetos/', include('aplicacoes.projetos.urls')),
    path('missoes/', include('aplicacoes.missoes.urls')),
    path('atividades/', include('aplicacoes.atividades.urls')),
    path('eventos/', include('aplicacoes.eventos.urls')),
    path('documentos/', include('aplicacoes.documentos.urls')),
    path('presenca/', include('aplicacoes.presenca.urls')),
    path('comunicacao/', include('aplicacoes.comunicacao.urls')),
    path('adimplencia/', include('aplicacoes.adimplencia.urls')),
    path('engajamento/', include('aplicacoes.engajamento.urls')),
    path('relatorios/', include('aplicacoes.relatorios.urls')),
    path('dicionario/', include('aplicacoes.dicionario.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
