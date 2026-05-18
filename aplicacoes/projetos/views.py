"""Views de Projetos — listagem e CRUD com permissão restrita a editores."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from aplicacoes.nucleo.servicos.auditoria import detectar_alteracoes, historico_de, registrar_criacao, registrar_edicao
from aplicacoes.projetos.forms import ProjetoForm
from aplicacoes.projetos.models import Projeto


def _eh_editor(request):
    """Retorna True se o usuário atual pode criar/editar projetos."""
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


@login_required
def lista_projetos(request):
    """Lista projetos com busca textual e filtros por status/fonte de recurso."""
    busca = request.GET.get('busca', '').strip()
    status = request.GET.get('status', '')
    fonte = request.GET.get('fonte', '')

    projetos = Projeto.objects.all()
    if busca:
        projetos = projetos.filter(
            Q(nome__icontains=busca) | Q(descricao__icontains=busca) | Q(objetivo__icontains=busca)
        )
    if status:
        projetos = projetos.filter(status=status)
    if fonte:
        projetos = projetos.filter(fonte_recurso=fonte)

    # KPIs do header
    total = Projeto.objects.count()
    em_andamento = Projeto.objects.filter(status=Projeto.Status.EM_ANDAMENTO).count()
    concluidos = Projeto.objects.filter(status=Projeto.Status.CONCLUIDO).count()
    em_planejamento = Projeto.objects.filter(status=Projeto.Status.PLANEJAMENTO).count()

    contexto = {
        'projetos': projetos,
        'busca': busca,
        'status_filtro': status, 'status_choices': Projeto.Status.choices,
        'fonte_filtro': fonte, 'fontes': Projeto.FontesRecurso.choices,
        'eh_editor': _eh_editor(request),
        'header_icone': 'clipboard-list', 'header_cor': 'cyan',
        'header_titulo': 'Projetos institucionais',
        'header_descricao': 'Iniciativas com escopo, prazo e responsáveis definidos. Têm começo, meio e fim — diferente de instâncias (permanentes) ou eventos (pontuais).',
        'header_kpis': [
            {'label': 'projetos', 'valor': total, 'cor': 'gray'},
            {'label': 'em andamento', 'valor': em_andamento, 'cor': 'blue'},
            {'label': 'concluídos', 'valor': concluidos, 'cor': 'emerald'},
            {'label': 'em planejamento', 'valor': em_planejamento, 'cor': 'amber'},
        ],
    }
    template = 'projetos/parciais/lista_projetos_tabela.html' if request.headers.get('HX-Request') else 'projetos/lista_projetos.html'
    return render(request, template, contexto)


@login_required
def detalhe_projeto(request, pk):
    """Detalhe do projeto: responsável (com município), pautas, instância e documentos."""
    projeto = get_object_or_404(Projeto, pk=pk)
    municipio_responsavel = None
    if projeto.responsavel:
        vinculo = projeto.responsavel.vinculos.filter(vigente=True).select_related('municipio').first()
        municipio_responsavel = vinculo.municipio if vinculo else None
    contexto = {
        'projeto': projeto,
        'municipio_responsavel': municipio_responsavel,
        'documentos': projeto.documentos.all()[:10],
        'historico': historico_de(projeto),
        'eh_editor': _eh_editor(request),
    }
    return render(request, 'projetos/detalhe_projeto.html', contexto)


@login_required
def criar_projeto(request):
    """Formulário de criação de projeto — restrito a editores."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para criar projetos.')
        return redirect('projetos:lista_projetos')
    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        if form.is_valid():
            projeto = form.save()
            registrar_criacao(request.user, projeto)
            messages.success(request, f'Projeto "{projeto.nome}" criado.')
            return redirect('projetos:lista_projetos')
    else:
        form = ProjetoForm()
    return render(request, 'projetos/form_projeto.html', {'form': form, 'projeto': None})


@login_required
def editar_projeto(request, pk):
    """Formulário de edição de projeto — restrito a editores."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para editar projetos.')
        return redirect('projetos:lista_projetos')
    projeto = get_object_or_404(Projeto, pk=pk)
    if request.method == 'POST':
        form = ProjetoForm(request.POST, instance=projeto)
        if form.is_valid():
            alteracoes = detectar_alteracoes(projeto, form.cleaned_data)
            form.save()
            registrar_edicao(request.user, projeto, alteracoes)
            messages.success(request, f'Projeto "{projeto.nome}" atualizado.')
            return redirect('projetos:lista_projetos')
    else:
        form = ProjetoForm(instance=projeto)
    return render(request, 'projetos/form_projeto.html', {'form': form, 'projeto': projeto})
