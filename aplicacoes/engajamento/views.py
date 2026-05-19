"""Views de engajamento — ranking com filtros + página de Metodologia."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from aplicacoes.cadastro.models import Municipio
from aplicacoes.engajamento.models import ConfiguracaoEngajamento, Engajamento, PesoEngajamento


ORDEM_PERMITIDA_ENGAJAMENTO = {
    'municipio__nome', 'bienio', 'pontuacao_normalizada',
    'pontuacao_bruta', 'total_participacoes', 'nivel',
}


@login_required
def lista_engajamento(request):
    """Lista engajamentos com busca, filtros e ordenação clicável."""
    busca = request.GET.get('busca', '').strip()
    nivel = request.GET.get('nivel', '')
    regiao = request.GET.get('regiao', '')
    ordem = request.GET.get('ordem', '-pontuacao_normalizada')

    engajamentos = Engajamento.objects.select_related('municipio')
    if busca:
        engajamentos = engajamentos.filter(
            Q(municipio__nome__icontains=busca) | Q(municipio__uf__icontains=busca)
        )
    if nivel:
        engajamentos = engajamentos.filter(nivel=nivel)
    if regiao:
        engajamentos = engajamentos.filter(municipio__regiao=regiao)

    campo_ordem = ordem.lstrip('-')
    if campo_ordem in ORDEM_PERMITIDA_ENGAJAMENTO:
        engajamentos = engajamentos.order_by(ordem, 'municipio__nome')
    else:
        engajamentos = engajamentos.order_by('-pontuacao_normalizada', 'municipio__nome')
        ordem = '-pontuacao_normalizada'

    ctx = {
        'engajamentos': engajamentos, 'busca': busca,
        'nivel_filtro': nivel, 'niveis': Engajamento.Nivel.choices,
        'regiao_filtro': regiao, 'regioes': Municipio.Regiao.choices,
        'ordem': ordem,
    }
    template = 'engajamento/parciais/lista_engajamento_tabela.html' if request.headers.get('HX-Request') else 'engajamento/lista_engajamento.html'
    return render(request, template, ctx)


@login_required
def indice_fnp_ranking(request):
    """Ranking dos municipios pelo Indice FNP composto.

    Combina engajamento, adimplencia, participacao e presenca em uma nota
    unica 0-100. Aceita filtros ?regiao= e ?uf= via GET.
    """
    from aplicacoes.engajamento.servicos.indice_fnp import PESOS, ranking_top
    regiao = request.GET.get('regiao', '')
    uf = request.GET.get('uf', '')
    ranking = ranking_top(limite=50, regiao=regiao or None, uf=uf or None)
    return render(request, 'engajamento/indice_fnp.html', {
        'ranking': ranking,
        'pesos': PESOS,
        'regiao_filtro': regiao,
        'uf_filtro': uf,
        'regioes': Municipio.Regiao.choices,
        'ufs': Municipio.UF_CHOICES,
    })


@login_required
def metodologia(request):
    """Página de Metodologia — explica como o engajamento é calculado.

    Mostra a configuração geral (meta, decaimento, penalidades) e a tabela
    de pesos por categoria. Todos os valores vêm do banco e podem ser
    ajustados pelo admin sem alteração de código.
    """
    config = ConfiguracaoEngajamento.atual()
    pesos = PesoEngajamento.objects.filter(ativo=True).order_by('chave')
    ctx = {
        'config': config,
        'pesos': pesos,
    }
    return render(request, 'engajamento/metodologia.html', ctx)
