"""Views do Dicionário — listagem agrupada por seção e API de busca por termo."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render

from .models import TermoDicionario


@login_required
def termo_json(request):
    """Endpoint JSON: ``?termo=instancia`` retorna definição se houver.

    Usado pelos ícones (?) clicáveis nos labels de formulário/listagem.
    """
    slug = (request.GET.get('termo') or '').strip()
    if not slug:
        return JsonResponse({'encontrado': False})
    # Busca tolerante: por termo exato ou contains (preserva acentos/case)
    obj = TermoDicionario.objects.filter(ativo=True).filter(
        Q(termo__iexact=slug) | Q(termo__icontains=slug)
    ).order_by('termo').first()
    if not obj:
        return JsonResponse({'encontrado': False, 'termo_buscado': slug})
    return JsonResponse({
        'encontrado': True,
        'termo': obj.termo,
        'secao': obj.get_secao_display(),
        'definicao': obj.definicao,
        'tipo_de_dado': obj.tipo_de_dado,
    })


@login_required
def lista_dicionario(request):
    """Lista todos os termos ativos do dicionário, agrupados por seção.

    Suporta busca textual via parâmetro ``busca`` e filtro por seção
    via ``secao``. O resultado é organizado em estrutura
    ``[(secao_label, [termos...]), ...]`` para facilitar a renderização.
    """
    busca = request.GET.get('busca', '').strip()
    secao_filtro = request.GET.get('secao', '')

    termos = TermoDicionario.objects.filter(ativo=True)
    if busca:
        termos = termos.filter(
            Q(termo__icontains=busca)
            | Q(definicao__icontains=busca)
            | Q(tipo_de_dado__icontains=busca)
        )
    if secao_filtro:
        termos = termos.filter(secao=secao_filtro)

    # Agrupa por seção preservando a ordem definida no model.
    secoes = {}
    for termo in termos:
        secoes.setdefault(termo.secao, []).append(termo)

    grupos = []
    for valor, label in TermoDicionario.Secao.choices:
        if valor in secoes:
            grupos.append((valor, label, secoes[valor]))

    contexto = {
        'grupos': grupos,
        'busca': busca,
        'secao_filtro': secao_filtro,
        'secoes_disponiveis': TermoDicionario.Secao.choices,
        'total': termos.count(),
    }
    return render(request, 'dicionario/lista_dicionario.html', contexto)
