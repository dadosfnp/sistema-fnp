"""Views de relatórios — painel de indicadores e futuras exportações."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def painel(request):
    """Renderiza o painel de relatórios gerenciais."""
    return render(request, 'relatorios/painel.html')
