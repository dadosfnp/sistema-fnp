"""Auditoria de LEITURA de dados sensíveis (LGPD Art. 37, 46).

Quando um usuário abre o detalhe de uma Pessoa, Visita ou CredenciamentoPrevio,
gravamos um ``LogAcessoSensivel`` com usuário + IP + entidade + timestamp.
Diferente da auditoria normal (que rastreia CRUD), aqui o objetivo é provar
*quem consultou o quê* — exigido para responder à ANPD em caso de incidente
ou para investigar exfiltração (ex: usuário consultando 500 pessoas em 10 min).

Aplicado como decorator:

    @registrar_leitura_sensivel(modelo='Pessoa', contexto='detalhe')
    def detalhe_pessoa(request, id):
        ...

O decorator extrai o ``id`` do kwargs e grava após a view rodar (não bloqueia
a resposta em caso de falha de log — apenas captura silenciosamente).
"""

import logging
from functools import wraps

logger = logging.getLogger(__name__)


def _ip_do_request(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def registrar_leitura_sensivel(modelo, contexto='detalhe', id_kwarg='id'):
    """Decorator que cria um LogAcessoSensivel após a view executar com sucesso.

    Args:
        modelo: Nome do model para fins de filtro no admin (ex: 'Pessoa').
        contexto: Identificador da operação (ex: 'detalhe', 'exportacao').
        id_kwarg: Nome do kwarg que contém o ID do objeto (default: 'id').
    """
    def decorador(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            response = view(request, *args, **kwargs)
            try:
                if (200 <= response.status_code < 300
                        and request.user.is_authenticated):
                    from aplicacoes.nucleo.models import LogAcessoSensivel
                    LogAcessoSensivel.objects.create(
                        usuario=request.user,
                        modelo=modelo,
                        objeto_id=str(kwargs.get(id_kwarg, ''))[:50],
                        ip=_ip_do_request(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                        contexto=contexto[:50],
                    )
            except Exception as exc:
                # Auditoria nao pode quebrar a resposta — apenas loga
                logger.warning('Falha ao registrar leitura sensivel: %s', exc)
            return response
        return wrapper
    return decorador
