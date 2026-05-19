"""Views de adimplência — listagem com busca e filtros, CRUD para editor."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from aplicacoes.adimplencia.forms import AdimplenciaForm
from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.nucleo.servicos.auditoria import detectar_alteracoes, registrar_criacao, registrar_edicao


def _eh_editor(request):
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


# Campos permitidos para ordenacao via ``?ordem=``. Allowlist evita SQL injection
# em order_by — qualquer slug fora dessa lista cai no default.
ORDEM_PERMITIDA_ADIMPLENCIA = {
    'municipio__nome', 'ano_referencia', 'status', 'valor_devido',
    'valor_pago', 'data_pagamento',
}


@login_required
def lista_adimplencia(request):
    """Lista adimplência com busca, filtros e ordenação clicável por coluna."""
    busca = request.GET.get('busca', '').strip()
    status = request.GET.get('status', '')
    ano = request.GET.get('ano', '')
    ordem = request.GET.get('ordem', '-ano_referencia')

    registros = Adimplencia.objects.select_related('municipio')
    if busca:
        registros = registros.filter(
            Q(municipio__nome__icontains=busca) | Q(municipio__uf__icontains=busca)
        )
    if status:
        registros = registros.filter(status=status)
    if ano:
        registros = registros.filter(ano_referencia=ano)

    # Sanitiza ordem: aceita campo permitido (com ou sem '-' prefix).
    campo_ordem = ordem.lstrip('-')
    if campo_ordem in ORDEM_PERMITIDA_ADIMPLENCIA:
        registros = registros.order_by(ordem, 'municipio__nome')
    else:
        registros = registros.order_by('-ano_referencia', 'municipio__nome')
        ordem = '-ano_referencia'

    status_choices = Adimplencia.Status.choices
    anos = Adimplencia.objects.values_list('ano_referencia', flat=True).distinct().order_by('-ano_referencia')
    ctx = {
        'registros': registros, 'busca': busca,
        'status_filtro': status, 'status_choices': status_choices,
        'ano_filtro': ano, 'anos': anos,
        'ordem': ordem,
    }
    template = 'adimplencia/parciais/lista_adimplencia_tabela.html' if request.headers.get('HX-Request') else 'adimplencia/lista_adimplencia.html'
    return render(request, template, ctx)


@login_required
def criar_adimplencia(request):
    """Formulário de criação de registro de adimplência."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao.')
        return redirect('adimplencia:lista_adimplencia')
    if request.method == 'POST':
        form = AdimplenciaForm(request.POST)
        if form.is_valid():
            obj = form.save()
            registrar_criacao(request.user, obj)
            messages.success(request, 'Registro de adimplencia criado.')
            return redirect('adimplencia:lista_adimplencia')
    else:
        form = AdimplenciaForm()
    return render(request, 'adimplencia/form_adimplencia.html', {'form': form, 'objeto': None})


@login_required
def editar_adimplencia(request, pk):
    """Formulário de edição de registro de adimplência."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao.')
        return redirect('adimplencia:lista_adimplencia')
    obj = get_object_or_404(Adimplencia, pk=pk)
    if request.method == 'POST':
        form = AdimplenciaForm(request.POST, instance=obj)
        if form.is_valid():
            alteracoes = detectar_alteracoes(obj, form.cleaned_data)
            form.save()
            registrar_edicao(request.user, obj, alteracoes)
            messages.success(request, 'Registro de adimplencia atualizado.')
            return redirect('adimplencia:lista_adimplencia')
    else:
        form = AdimplenciaForm(instance=obj)
    return render(request, 'adimplencia/form_adimplencia.html', {'form': form, 'objeto': obj})
