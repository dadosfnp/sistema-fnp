"""Views de eventos — listagem com busca e detalhe com participações confirmadas."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from aplicacoes.eventos.models import Evento


@login_required
def lista_eventos(request):
    """Lista eventos com busca por título, local ou tipo. Suporta HTMX."""
    busca = request.GET.get('busca', '').strip()
    eventos = Evento.objects.all().order_by('-data_inicio')
    if busca:
        eventos = eventos.filter(
            Q(titulo__icontains=busca)
            | Q(local__icontains=busca)
            | Q(tipo__icontains=busca)
        )
    template = 'eventos/parciais/lista_eventos_tabela.html' if request.headers.get('HX-Request') else 'eventos/lista_eventos.html'
    return render(request, template, {'eventos': eventos, 'busca': busca})


@login_required
def detalhe_evento(request, pk):
    """Exibe detalhes de um evento com lista de participações confirmadas."""
    evento = get_object_or_404(Evento, pk=pk)
    participacoes = evento.participacoes.select_related('pessoa', 'municipio').filter(confirmado=True).order_by('pessoa__nome')
    return render(request, 'eventos/detalhe_evento.html', {
        'evento': evento,
        'participacoes': participacoes,
    })
