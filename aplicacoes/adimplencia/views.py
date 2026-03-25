"""Views de adimplência — listagem com busca por município, UF ou status."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from aplicacoes.adimplencia.models import Adimplencia


@login_required
def lista_adimplencia(request):
    """Lista registros de adimplência com busca e suporte a HTMX."""
    busca = request.GET.get('busca', '').strip()
    registros = Adimplencia.objects.select_related('municipio').order_by('-ano_referencia', 'municipio__nome')
    if busca:
        registros = registros.filter(
            Q(municipio__nome__icontains=busca)
            | Q(municipio__uf__icontains=busca)
            | Q(status__icontains=busca)
        )
    template = 'adimplencia/parciais/lista_adimplencia_tabela.html' if request.headers.get('HX-Request') else 'adimplencia/lista_adimplencia.html'
    return render(request, template, {'registros': registros, 'busca': busca})
