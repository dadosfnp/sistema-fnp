"""Views de eventos — listagem, detalhe, CRUD de evento e participação."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from aplicacoes.eventos.forms import EventoForm, ParticipacaoForm
from aplicacoes.eventos.models import Evento, Participacao
from aplicacoes.nucleo.servicos.auditoria import detectar_alteracoes, historico_de, registrar_criacao, registrar_edicao


def _eh_editor(request):
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


@login_required
def lista_eventos(request):
    """Lista eventos com busca e filtros por tipo e modalidade."""
    busca = request.GET.get('busca', '').strip()
    tipo = request.GET.get('tipo', '')
    modalidade = request.GET.get('modalidade', '')
    eventos = Evento.objects.all().order_by('-data_inicio')
    if busca:
        eventos = eventos.filter(Q(titulo__icontains=busca) | Q(local__icontains=busca))
    if tipo:
        eventos = eventos.filter(tipo=tipo)
    if modalidade:
        eventos = eventos.filter(modalidade=modalidade)
    from django.utils import timezone
    hoje = timezone.now().date()
    total = Evento.objects.count()
    futuros = Evento.objects.filter(data_inicio__gte=hoje).count()
    presenciais = Evento.objects.filter(modalidade=Evento.Modalidade.PRESENCIAL).count()
    online = Evento.objects.filter(modalidade=Evento.Modalidade.ONLINE).count()

    ctx = {
        'eventos': eventos, 'busca': busca,
        'tipo_filtro': tipo, 'tipos': Evento.TipoEvento.choices,
        'modalidade_filtro': modalidade, 'modalidades': Evento.Modalidade.choices,
        'header_icone': 'calendar-days', 'header_cor': 'purple',
        'header_titulo': 'Eventos institucionais',
        'header_descricao': 'Acontecimentos pontuais — assembleias, audiências, congressos, seminários. Cada evento tem pontuação de engajamento configurável por modalidade e papel.',
        'header_kpis': [
            {'label': 'eventos', 'valor': total, 'cor': 'gray'},
            {'label': 'futuros', 'valor': futuros, 'cor': 'blue'},
            {'label': 'presenciais', 'valor': presenciais, 'cor': 'emerald'},
            {'label': 'online', 'valor': online, 'cor': 'sky'},
        ],
    }
    template = 'eventos/parciais/lista_eventos_tabela.html' if request.headers.get('HX-Request') else 'eventos/lista_eventos.html'
    return render(request, template, ctx)


@login_required
def detalhe_evento(request, pk):
    """Exibe detalhes do evento com participações confirmadas."""
    evento = get_object_or_404(Evento, pk=pk)
    participacoes = evento.participacoes.select_related('pessoa', 'municipio').filter(confirmado=True).order_by('pessoa__nome')
    return render(request, 'eventos/detalhe_evento.html', {
        'evento': evento, 'participacoes': participacoes,
        'historico': historico_de(evento),
    })


@login_required
def criar_evento(request):
    """Formulário de criação de evento."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao.')
        return redirect('eventos:lista_eventos')
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save()
            registrar_criacao(request.user, evento)
            messages.success(request, f'Evento "{evento.titulo}" criado.')
            return redirect('eventos:detalhe_evento', pk=evento.pk)
    else:
        form = EventoForm()
    return render(request, 'eventos/form_evento.html', {'form': form, 'evento': None})


@login_required
def editar_evento(request, pk):
    """Formulário de edição de evento."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao.')
        return redirect('eventos:detalhe_evento', pk=pk)
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            alteracoes = detectar_alteracoes(evento, form.cleaned_data)
            form.save()
            registrar_edicao(request.user, evento, alteracoes)
            messages.success(request, f'Evento "{evento.titulo}" atualizado.')
            return redirect('eventos:detalhe_evento', pk=pk)
    else:
        form = EventoForm(instance=evento)
    return render(request, 'eventos/form_evento.html', {'form': form, 'evento': evento})


@login_required
def criar_participacao(request, evento_pk=None):
    """Formulário de registro de participação."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao.')
        return redirect('eventos:lista_eventos')
    initial = {}
    if evento_pk:
        initial['evento'] = get_object_or_404(Evento, pk=evento_pk)
    if request.method == 'POST':
        form = ParticipacaoForm(request.POST)
        if form.is_valid():
            participacao = form.save()
            registrar_criacao(request.user, participacao)
            messages.success(request, f'Participacao de {participacao.pessoa.nome} registrada.')
            return redirect('eventos:detalhe_evento', pk=participacao.evento.pk)
    else:
        form = ParticipacaoForm(initial=initial)
    return render(request, 'eventos/form_participacao.html', {'form': form})


@login_required
def editar_participacao(request, pk):
    """Formulário de edição de participação."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao.')
        return redirect('eventos:lista_eventos')
    participacao = get_object_or_404(Participacao, pk=pk)
    if request.method == 'POST':
        form = ParticipacaoForm(request.POST, instance=participacao)
        if form.is_valid():
            alteracoes = detectar_alteracoes(participacao, form.cleaned_data)
            form.save()
            registrar_edicao(request.user, participacao, alteracoes)
            messages.success(request, 'Participacao atualizada.')
            return redirect('eventos:detalhe_evento', pk=participacao.evento.pk)
    else:
        form = ParticipacaoForm(instance=participacao)
    return render(request, 'eventos/form_participacao.html', {'form': form})
