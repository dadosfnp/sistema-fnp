"""Middleware de roteamento por perfil — separa portal externo (prefeito) da app FNP.

Quando o usuario tem perfil tipo='prefeito' e municipio_vinculado != None,
qualquer rota fora de ``/portal/`` redireciona para ``/portal/`` (com excecao
de logout, admin etc). Isso isola o portal externo da operacao interna sem
duplicar codigo.
"""

from django.conf import settings
from django.http import HttpResponseRedirect

# Rotas permitidas para perfil "prefeito" (alem de /portal/)
ROTAS_LIBERADAS_PREFEITO = (
    '/portal/',
    '/entrar/',
    '/sair/',
    '/static/',
    '/media/',
    '/dicionario/api/',
)


class IsolarPortalPrefeitoMiddleware:
    """Redireciona prefeitos para /portal/ caso tentem acessar outras areas."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Defer auth e perfil checks para usuarios autenticados
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and not user.is_superuser:
            perfil = getattr(user, 'perfil', None)
            if perfil and perfil.tipo == 'prefeito':
                path = request.path
                if not any(path.startswith(r) for r in ROTAS_LIBERADAS_PREFEITO):
                    return HttpResponseRedirect('/portal/')
        return self.get_response(request)
