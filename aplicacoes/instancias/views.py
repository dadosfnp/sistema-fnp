"""Views de Instâncias — listagem e CRUD de Espaços de Diálogo Federativo.

A criação e edição são restritas a usuários com perfil de editor (ou superusers),
seguindo o mesmo padrão usado em ``eventos``.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from aplicacoes.instancias.forms import InstanciaForm
from aplicacoes.instancias.models import Instancia
from aplicacoes.nucleo.servicos.auditoria import detectar_alteracoes, historico_de, registrar_criacao, registrar_edicao


def _eh_editor(request):
    """Retorna True se o usuário atual pode criar/editar instâncias."""
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


@login_required
def lista_instancias(request):
    """Lista instâncias com busca textual e filtros por origem/forma/status."""
    busca = request.GET.get('busca', '').strip()
    origem = request.GET.get('origem', '')
    forma = request.GET.get('forma', '')
    status = request.GET.get('status', '')

    instancias = Instancia.objects.all()
    if busca:
        instancias = instancias.filter(
            Q(nome__icontains=busca) | Q(descricao__icontains=busca) | Q(numero_arcabouco__icontains=busca)
        )
    if origem:
        instancias = instancias.filter(origem=origem)
    if forma:
        instancias = instancias.filter(forma=forma)
    if status:
        instancias = instancias.filter(status=status)

    # KPIs do header
    total = Instancia.objects.count()
    em_funcionamento = Instancia.objects.filter(status=Instancia.Status.EM_FUNCIONAMENTO).count()
    internas = Instancia.objects.filter(origem=Instancia.Origem.INTERNA).count()
    externas = Instancia.objects.filter(origem=Instancia.Origem.EXTERNA).count()

    contexto = {
        'instancias': instancias,
        'busca': busca,
        'origem_filtro': origem, 'origens': Instancia.Origem.choices,
        'forma_filtro': forma, 'formas': Instancia.Forma.choices,
        'status_filtro': status, 'status_choices': Instancia.Status.choices,
        'eh_editor': _eh_editor(request),
        'header_icone': 'messages-square', 'header_cor': 'indigo',
        'header_titulo': 'Espaços de Diálogo Federativo',
        'header_descricao': 'Estruturas institucionais — conselhos, comissões, fóruns — onde a FNP atua ou tem representação. Cada instância tem arcabouço legal, periodicidade de reuniões e composição definida.',
        'header_kpis': [
            {'label': 'instâncias', 'valor': total, 'cor': 'gray'},
            {'label': 'em funcionamento', 'valor': em_funcionamento, 'cor': 'emerald'},
            {'label': 'internas', 'valor': internas, 'cor': 'indigo'},
            {'label': 'externas', 'valor': externas, 'cor': 'amber'},
        ],
    }
    template = 'instancias/parciais/lista_instancias_tabela.html' if request.headers.get('HX-Request') else 'instancias/lista_instancias.html'
    return render(request, template, contexto)


@login_required
def detalhe_instancia(request, pk):
    """Exibe a instância com representações, atividades, eventos e documentos vinculados."""
    instancia = get_object_or_404(Instancia, pk=pk)
    contexto = {
        'instancia': instancia,
        'representacoes': instancia.representacoes.select_related('pessoa').order_by('-vigente', '-inicio_mandato'),
        'atividades': instancia.atividades.order_by('-data_reuniao')[:20],
        'eventos_vinculados': instancia.eventos_vinculados.order_by('-data_inicio')[:10],
        'documentos': instancia.documentos.all()[:10],
        'subgrupos': instancia.subgrupos.all(),
        'historico': historico_de(instancia),
        'eh_editor': _eh_editor(request),
    }
    return render(request, 'instancias/detalhe_instancia.html', contexto)


@login_required
def criar_instancia(request):
    """Formulário de criação de instância — restrito a editores."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para criar instancias.')
        return redirect('instancias:lista_instancias')
    if request.method == 'POST':
        form = InstanciaForm(request.POST)
        if form.is_valid():
            instancia = form.save()
            registrar_criacao(request.user, instancia)
            messages.success(request, f'Instancia "{instancia.nome}" criada.')
            return redirect('instancias:lista_instancias')
    else:
        form = InstanciaForm()
    return render(request, 'instancias/form_instancia.html', {'form': form, 'instancia': None})


@login_required
def editar_instancia(request, pk):
    """Formulário de edição de instância — restrito a editores."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para editar instancias.')
        return redirect('instancias:lista_instancias')
    instancia = get_object_or_404(Instancia, pk=pk)
    if request.method == 'POST':
        form = InstanciaForm(request.POST, instance=instancia)
        if form.is_valid():
            alteracoes = detectar_alteracoes(instancia, form.cleaned_data)
            form.save()
            registrar_edicao(request.user, instancia, alteracoes)
            messages.success(request, f'Instancia "{instancia.nome}" atualizada.')
            return redirect('instancias:lista_instancias')
    else:
        form = InstanciaForm(instance=instancia)
    return render(request, 'instancias/form_instancia.html', {'form': form, 'instancia': instancia})
