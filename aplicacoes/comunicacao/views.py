"""Views de Comunicação — composição via modal HTMX e envio de mala direta por entidade.

A view ``compor_envio_modal`` renderiza um *partial* HTMX que pode ser
embutido como modal em qualquer página de detalhe. ``processar_envio``
executa o disparo SMTP e retorna o fragmento de confirmação que substitui
o conteúdo do modal. ``historico_envios`` permanece como página dedicada
para auditoria.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMessage, get_connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import Context, Template

from aplicacoes.comunicacao.models import Envio, TemplateEmail
from aplicacoes.comunicacao.servicos import categoria_para_entidade, coletar_destinatarios


def _eh_editor(request):
    """Retorna True se o usuário pode disparar mala direta."""
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


def _resolver_entidade(app_label, model_name, object_id):
    """Resolve a entidade dona da mala direta via ContentType + object_id."""
    content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    model_class = content_type.model_class()
    entidade = get_object_or_404(model_class, pk=object_id)
    return content_type, entidade


def _renderizar(texto, contexto):
    """Renderiza um string com placeholders Django ({{ ... }}) usando contexto dado."""
    return Template(texto).render(Context(contexto))


def _contexto_modal(request, app_label, model_name, object_id):
    """Monta o contexto comum usado em todos os renders do modal."""
    content_type, entidade = _resolver_entidade(app_label, model_name, object_id)
    destinatarios = coletar_destinatarios(entidade)
    categoria = categoria_para_entidade(entidade)
    templates = TemplateEmail.objects.filter(ativo=True).filter(
        categoria__in=[categoria, TemplateEmail.Categoria.GERAL],
    ).order_by('nome')
    template_id = request.GET.get('template') or request.POST.get('template')
    template_selecionado = templates.filter(pk=template_id).first() if template_id else None
    return {
        'content_type': content_type,
        'entidade': entidade,
        'destinatarios': destinatarios,
        'templates': templates,
        'template_selecionado': template_selecionado,
        'app_label': app_label,
        'model_name': model_name,
        'object_id': object_id,
    }


@login_required
def compor_envio_modal(request, app_label, model_name, object_id):
    """Renderiza o conteúdo do modal de mala direta (parcial HTMX).

    Aceita ``?template=<pk>`` no querystring para pré-carregar um template.
    Sempre retorna apenas o fragmento HTML que vai dentro do modal — o
    container do modal fica no template da entidade.
    """
    if not _eh_editor(request):
        return HttpResponse('Sem permissão.', status=403)

    ctx = _contexto_modal(request, app_label, model_name, object_id)
    template = ctx['template_selecionado']
    ctx['assunto'] = template.assunto if template else ''
    ctx['corpo'] = template.corpo if template else ''
    return render(request, 'comunicacao/parciais/modal_envio.html', ctx)


@login_required
def processar_envio(request, app_label, model_name, object_id):
    """Executa o disparo da mala direta a partir do modal HTMX.

    Em sucesso, retorna fragmento de confirmação que substitui o conteúdo
    do modal. Em falha de envio, retorna o modal com mensagem de erro
    visível para o usuário.
    """
    if not _eh_editor(request):
        return HttpResponse('Sem permissão.', status=403)
    if request.method != 'POST':
        return HttpResponse(status=405)

    ctx = _contexto_modal(request, app_label, model_name, object_id)
    content_type = ctx['content_type']
    entidade = ctx['entidade']
    destinatarios = ctx['destinatarios']

    assunto_template = request.POST.get('assunto', '').strip()
    corpo_template = request.POST.get('corpo', '').strip()
    anexo = request.FILES.get('anexo')

    if not destinatarios:
        ctx.update({'assunto': assunto_template, 'corpo': corpo_template,
                    'erro_form': 'Nenhum destinatário válido.'})
        return render(request, 'comunicacao/parciais/modal_envio.html', ctx)

    emails_disparados = []
    try:
        connection = get_connection()
        connection.open()
        for dest in destinatarios:
            placeholders = {
                'entidade': str(entidade),
                'pessoa': dest['pessoa'].nome,
                'municipio': str(dest['municipio']) if dest['municipio'] else '',
            }
            assunto = _renderizar(assunto_template, placeholders)
            corpo = _renderizar(corpo_template, placeholders)
            email = EmailMessage(
                subject=assunto,
                body=corpo,
                to=[dest['email']],
                connection=connection,
            )
            if anexo:
                email.attach(anexo.name, anexo.read(), anexo.content_type)
                anexo.seek(0)
            email.send(fail_silently=False)
            emails_disparados.append(dest['email'])
        connection.close()
        envio = Envio.objects.create(
            content_type=content_type,
            object_id=object_id,
            template=ctx['template_selecionado'],
            assunto=assunto_template,
            corpo=corpo_template,
            destinatarios=emails_disparados,
            total_destinatarios=len(emails_disparados),
            status=Envio.StatusEnvio.ENVIADO,
            enviado_por=request.user,
            anexo=anexo,
        )
        return render(request, 'comunicacao/parciais/modal_sucesso.html', {
            'envio': envio,
            'app_label': app_label,
            'model_name': model_name,
            'object_id': object_id,
        })
    except Exception as exc:
        Envio.objects.create(
            content_type=content_type, object_id=object_id,
            template=ctx['template_selecionado'],
            assunto=assunto_template, corpo=corpo_template,
            destinatarios=emails_disparados,
            total_destinatarios=len(emails_disparados),
            status=Envio.StatusEnvio.FALHA,
            enviado_por=request.user, erro=str(exc),
        )
        ctx.update({'assunto': assunto_template, 'corpo': corpo_template,
                    'erro_form': f'Falha ao enviar: {exc}'})
        return render(request, 'comunicacao/parciais/modal_envio.html', ctx)


@login_required
def compor_envio(request, app_label, model_name, object_id):
    """Página dedicada de composição — mantida como fallback (sem JS)."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para enviar mala direta.')
        return redirect('nucleo:inicio')

    ctx = _contexto_modal(request, app_label, model_name, object_id)
    template = ctx['template_selecionado']
    ctx['assunto'] = request.POST.get('assunto') or (template.assunto if template else '')
    ctx['corpo'] = request.POST.get('corpo') or (template.corpo if template else '')

    if request.method == 'POST' and 'enviar' in request.POST:
        # Reutiliza o pipeline do modal e redireciona para o histórico em sucesso.
        request.method = 'POST'
        resposta = processar_envio(request, app_label, model_name, object_id)
        # ``processar_envio`` retorna HTML do modal; aqui forçamos redirect.
        if resposta.status_code == 200 and 'Mensagem enviada' in resposta.content.decode('utf-8', errors='ignore'):
            return redirect(
                'comunicacao:historico_envios',
                app_label=app_label, model_name=model_name, object_id=object_id,
            )

    return render(request, 'comunicacao/form_envio.html', ctx)


@login_required
def historico_envios(request, app_label, model_name, object_id):
    """Lista os envios já realizados a partir de uma entidade."""
    content_type, entidade = _resolver_entidade(app_label, model_name, object_id)
    envios = Envio.objects.filter(
        content_type=content_type, object_id=object_id,
    ).select_related('enviado_por', 'template').order_by('-criado_em')
    contexto = {
        'entidade': entidade,
        'envios': envios,
        'app_label': app_label,
        'model_name': model_name,
        'object_id': object_id,
        'eh_editor': _eh_editor(request),
    }
    return render(request, 'comunicacao/historico_envios.html', contexto)
