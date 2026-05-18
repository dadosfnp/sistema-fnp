"""Views de Missões — listagem e CRUD com permissão restrita a editores."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from aplicacoes.missoes.forms import MissaoForm
from aplicacoes.missoes.models import Missao
from aplicacoes.nucleo.servicos.auditoria import detectar_alteracoes, historico_de, registrar_criacao, registrar_edicao


def _eh_editor(request):
    """Retorna True se o usuário atual pode criar/editar missões."""
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


@login_required
def lista_missoes(request):
    """Lista missões com busca textual e filtros por tipo/status."""
    busca = request.GET.get('busca', '').strip()
    tipo = request.GET.get('tipo', '')
    status = request.GET.get('status', '')

    missoes = Missao.objects.all()
    if busca:
        missoes = missoes.filter(
            Q(titulo__icontains=busca) | Q(cidade__icontains=busca)
            | Q(pais__icontains=busca) | Q(objetivo__icontains=busca)
        )
    if tipo:
        missoes = missoes.filter(tipo=tipo)
    if status:
        missoes = missoes.filter(status=status)

    # KPIs do header
    total = Missao.objects.count()
    internacionais = Missao.objects.filter(tipo=Missao.Tipo.INTERNACIONAL).count()
    nacionais = Missao.objects.filter(tipo=Missao.Tipo.NACIONAL).count()
    realizadas = Missao.objects.filter(status=Missao.Status.REALIZADA).count()

    contexto = {
        'missoes': missoes,
        'busca': busca,
        'tipo_filtro': tipo, 'tipos': Missao.Tipo.choices,
        'status_filtro': status, 'status_choices': Missao.Status.choices,
        'eh_editor': _eh_editor(request),
        'header_icone': 'plane-takeoff', 'header_cor': 'rose',
        'header_titulo': 'Missões institucionais',
        'header_descricao': 'Deslocamentos da FNP com objetivo específico — viagens, intercâmbios técnicos, encontros nacionais ou internacionais. Cada missão tem uma delegação e gera relatório final.',
        'header_kpis': [
            {'label': 'missões', 'valor': total, 'cor': 'gray'},
            {'label': 'internacionais', 'valor': internacionais, 'cor': 'indigo'},
            {'label': 'nacionais', 'valor': nacionais, 'cor': 'blue'},
            {'label': 'realizadas', 'valor': realizadas, 'cor': 'emerald'},
        ],
    }
    template = 'missoes/parciais/lista_missoes_tabela.html' if request.headers.get('HX-Request') else 'missoes/lista_missoes.html'
    return render(request, template, contexto)


@login_required
def detalhe_missao(request, pk):
    """Detalhe da missão: delegação (com município de cada membro), documentos e vínculo."""
    missao = get_object_or_404(Missao, pk=pk)
    membros_qs = missao.delegacao.select_related('pessoa').all()
    membros = []
    for membro in membros_qs:
        vinculo = membro.pessoa.vinculos.filter(vigente=True).select_related('municipio').first()
        membros.append({
            'pessoa': membro.pessoa,
            'papel': membro.get_papel_display(),
            'observacao': membro.observacao,
            'municipio': vinculo.municipio if vinculo else None,
        })
    contexto = {
        'missao': missao,
        'membros': membros,
        'documentos': missao.documentos.all()[:10],
        'historico': historico_de(missao),
        'eh_editor': _eh_editor(request),
    }
    return render(request, 'missoes/detalhe_missao.html', contexto)


@login_required
def criar_missao(request):
    """Formulário de criação de missão — restrito a editores."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para criar missoes.')
        return redirect('missoes:lista_missoes')
    if request.method == 'POST':
        form = MissaoForm(request.POST)
        if form.is_valid():
            missao = form.save()
            registrar_criacao(request.user, missao)
            messages.success(request, f'Missao "{missao.titulo}" criada.')
            return redirect('missoes:lista_missoes')
    else:
        form = MissaoForm()
    return render(request, 'missoes/form_missao.html', {'form': form, 'missao': None})


@login_required
def editar_missao(request, pk):
    """Formulário de edição de missão — restrito a editores."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para editar missoes.')
        return redirect('missoes:lista_missoes')
    missao = get_object_or_404(Missao, pk=pk)
    if request.method == 'POST':
        form = MissaoForm(request.POST, instance=missao)
        if form.is_valid():
            alteracoes = detectar_alteracoes(missao, form.cleaned_data)
            form.save()
            registrar_edicao(request.user, missao, alteracoes)
            messages.success(request, f'Missao "{missao.titulo}" atualizada.')
            return redirect('missoes:lista_missoes')
    else:
        form = MissaoForm(instance=missao)
    return render(request, 'missoes/form_missao.html', {'form': form, 'missao': missao})
