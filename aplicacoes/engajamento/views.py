"""Views de engajamento — ranking com filtros por nível e região."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from aplicacoes.cadastro.models import Municipio
from aplicacoes.engajamento.models import Engajamento


@login_required
def lista_engajamento(request):
    """Lista engajamentos com busca e filtros por nível e região."""
    busca = request.GET.get('busca', '').strip()
    nivel = request.GET.get('nivel', '')
    regiao = request.GET.get('regiao', '')
    engajamentos = Engajamento.objects.select_related('municipio').order_by('-pontuacao_bruta')
    if busca:
        engajamentos = engajamentos.filter(
            Q(municipio__nome__icontains=busca) | Q(municipio__uf__icontains=busca)
        )
    if nivel:
        engajamentos = engajamentos.filter(nivel=nivel)
    if regiao:
        engajamentos = engajamentos.filter(municipio__regiao=regiao)
    ctx = {
        'engajamentos': engajamentos, 'busca': busca,
        'nivel_filtro': nivel, 'niveis': Engajamento.Nivel.choices,
        'regiao_filtro': regiao, 'regioes': Municipio.Regiao.choices,
    }
    template = 'engajamento/parciais/lista_engajamento_tabela.html' if request.headers.get('HX-Request') else 'engajamento/lista_engajamento.html'
    return render(request, template, ctx)
