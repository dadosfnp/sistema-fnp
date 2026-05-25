"""Views LGPD — termo de uso, política de privacidade, exportar/excluir dados.

Tudo o que o titular dos dados precisa exercer seus direitos LGPD (Art. 18):
- Conhecer a política → ``politica_privacidade`` (público)
- Aceitar/re-aceitar termos → ``termo_de_uso`` (autenticado)
- Exportar seus dados → ``exportar_meus_dados`` (autenticado)
- Solicitar exclusão → ``solicitar_exclusao`` (autenticado)

Mantemos rastro mínimo do aceite (IP + UA) — necessário para provar
consentimento em fiscalização ANPD, sem virar log abusivo.
"""

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from aplicacoes.nucleo.models import AceiteTermo, SolicitacaoExclusao


def _ip_do_request(request):
    """Extrai o IP real considerando proxies (X-Forwarded-For)."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def politica_privacidade(request):
    """Política de privacidade pública — acessível sem login (LGPD Art. 9º)."""
    return render(request, 'nucleo/politica_privacidade.html', {
        'versao': AceiteTermo.VERSAO_ATUAL,
        'atualizado_em': '2026-05-25',
    })


@login_required
def termo_de_uso(request):
    """Tela bloqueante de aceite do termo + política.

    GET renderiza o termo. POST grava o ``AceiteTermo`` e redireciona para
    ``?next=`` (ou ``/``). Sem aceite, ``ExigirAceiteTermoMiddleware`` mantém
    o usuário aqui — não dá para passar sem clicar.
    """
    proximo = request.GET.get('next', '/') or '/'
    if request.method == 'POST':
        if request.POST.get('aceito') != 'sim':
            return render(request, 'nucleo/termo_de_uso.html', {
                'versao': AceiteTermo.VERSAO_ATUAL,
                'proximo': proximo,
                'erro': 'É preciso marcar "Li e concordo" para continuar.',
            })
        AceiteTermo.objects.get_or_create(
            usuario=request.user,
            versao=AceiteTermo.VERSAO_ATUAL,
            defaults={
                'ip': _ip_do_request(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:255],
            },
        )
        return redirect(proximo)

    return render(request, 'nucleo/termo_de_uso.html', {
        'versao': AceiteTermo.VERSAO_ATUAL,
        'proximo': proximo,
    })


@login_required
def exportar_meus_dados(request):
    """Exporta em JSON todos os dados pessoais que o sistema mantém sobre o usuário.

    LGPD Art. 18, II (acesso aos dados) + Art. 9º (transparência). Não
    exportamos PII de outras pessoas — apenas o que o próprio usuário gerou
    ou onde figura como titular.
    """
    u = request.user
    perfil = getattr(u, 'perfil', None)

    dados = {
        'usuario': {
            'username': u.username,
            'nome_completo': u.get_full_name(),
            'email': u.email,
            'data_cadastro': u.date_joined.isoformat() if u.date_joined else None,
            'ultimo_login': u.last_login.isoformat() if u.last_login else None,
        },
        'perfil': None,
        'aceites_termo': list(
            AceiteTermo.objects.filter(usuario=u).values(
                'versao', 'ip', 'aceito_em',
            )
        ),
        'filtros_salvos': list(u.filtros_salvos.values('escopo', 'nome', 'parametros', 'criado_em')),
        'envios_realizados': list(
            u.envios_realizados.values(
                'id', 'assunto', 'total_destinatarios', 'status', 'canal', 'criado_em',
            )
        ),
        'logs_alteracao': list(
            u.logs_alteracao.values('acao', 'modelo', 'objeto_repr', 'data')[:500]
        ),
        'exportado_em': timezone.now().isoformat(),
    }
    if perfil:
        dados['perfil'] = {
            'tipo': perfil.tipo,
            'permissoes_extras': perfil.permissoes_extras,
            'municipio_vinculado': str(perfil.municipio_vinculado) if perfil.municipio_vinculado_id else None,
        }

    body = json.dumps(dados, ensure_ascii=False, indent=2, default=str)
    resp = HttpResponse(body, content_type='application/json; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="meus-dados-fnp-{timezone.now():%Y%m%d}.json"'
    return resp


@login_required
def aguardando_aprovacao(request):
    """Tela final para perfis pendentes/expirados/bloqueados.

    Aqui o usuário Google externo cai depois do OAuth — mostra mensagem
    institucional, contato do DPO e botão de sair. Não vaza nada do BD.
    """
    perfil = getattr(request.user, 'perfil', None)
    status = perfil.get_status_aprovacao_display() if perfil else 'sem perfil'
    return render(request, 'nucleo/aguardando_aprovacao.html', {
        'status': status,
        'expira_em': perfil.expira_em if perfil else None,
    })


@login_required
def solicitar_exclusao(request):
    """Registra pedido formal de exclusão de dados (LGPD Art. 18, VI).

    Não excluímos imediatamente — DPO precisa validar se há obrigação legal
    de retenção (ex: histórico de envios institucionais relevantes para
    auditoria pública). A solicitação fica visível no admin e o usuário
    recebe retorno por e-mail.
    """
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()[:2000]
        SolicitacaoExclusao.objects.create(
            usuario=request.user,
            email_contato=request.user.email or '',
            motivo=motivo,
        )
        return render(request, 'nucleo/exclusao_solicitada.html')

    return render(request, 'nucleo/solicitar_exclusao.html')
