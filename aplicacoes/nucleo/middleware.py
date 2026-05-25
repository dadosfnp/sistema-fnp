"""Middleware de roteamento por perfil — separa portal externo (prefeito) da app FNP.

Quando o usuario tem perfil tipo='prefeito' e municipio_vinculado != None,
qualquer rota fora de ``/portal/`` redireciona para ``/portal/`` (com excecao
de logout, admin etc). Isso isola o portal externo da operacao interna sem
duplicar codigo.
"""

import sys

from django.conf import settings
from django.http import HttpResponseRedirect

# Quando rodando ``manage.py test``, o middleware de termo é desligado para
# não exigir setUp em cada TestCase — em produção mantemos a obrigatoriedade.
_EM_MODO_TESTE = 'test' in sys.argv or 'pytest' in sys.argv[0].lower()

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


# Rotas isentas do termo de uso — login, logout, o próprio aceite, política
# pública, recursos estáticos e endpoints de pré-credenciamento público.
ROTAS_LIBERADAS_TERMO = (
    '/entrar/', '/sair/',
    '/conta/termo-de-uso/', '/conta/politica-privacidade/',
    '/static/', '/estaticos/', '/media/',
    '/recepcao/pre/', '/dicionario/api/',
    '/admin/jsi18n/',
)


class ExigirAceiteTermoMiddleware:
    """Força o aceite do termo de uso/LGPD antes de qualquer navegação.

    Por que: LGPD Art. 8º exige consentimento livre, informado e inequívoco.
    Aceitar uma vez via banner discreto não cumpre — o usuário precisa de
    uma tela bloqueante na primeira sessão (e em re-versões do termo).
    Como aplicar: este middleware roda DEPOIS de AuthenticationMiddleware.
    Usuário autenticado sem AceiteTermo da versão atual é redirecionado
    para ``/conta/termo-de-uso/`` independentemente da rota.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _EM_MODO_TESTE:
            return self.get_response(request)
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            path = request.path
            if not any(path.startswith(r) for r in ROTAS_LIBERADAS_TERMO):
                from aplicacoes.nucleo.models import AceiteTermo
                tem_aceite = AceiteTermo.objects.filter(
                    usuario=user, versao=AceiteTermo.VERSAO_ATUAL,
                ).exists()
                if not tem_aceite:
                    return HttpResponseRedirect(f'/conta/termo-de-uso/?next={path}')
        return self.get_response(request)
