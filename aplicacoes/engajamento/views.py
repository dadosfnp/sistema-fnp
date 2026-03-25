"""Views de engajamento — ranking de municípios por pontuação."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from aplicacoes.engajamento.models import Engajamento


@login_required
def lista_engajamento(request):
    """Lista engajamentos ordenados por pontuação com busca e suporte a HTMX."""
    busca = request.GET.get('busca', '').strip()
    engajamentos = Engajamento.objects.select_related('municipio').order_by('-pontuacao_bruta')
    if busca:
        engajamentos = engajamentos.filter(
            Q(municipio__nome__icontains=busca)
            | Q(municipio__uf__icontains=busca)
            | Q(nivel__icontains=busca)
        )
    template = 'engajamento/parciais/lista_engajamento_tabela.html' if request.headers.get('HX-Request') else 'engajamento/lista_engajamento.html'
    return render(request, template, {'engajamentos': engajamentos, 'busca': busca})
