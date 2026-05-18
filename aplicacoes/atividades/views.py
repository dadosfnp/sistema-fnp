"""Views de Atividades — listagem e CRUD com permissão restrita a editores."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from aplicacoes.atividades.forms import AtividadeForm
from aplicacoes.atividades.models import Atividade
from aplicacoes.instancias.models import Instancia
from aplicacoes.nucleo.servicos.auditoria import detectar_alteracoes, historico_de, registrar_criacao, registrar_edicao


def _eh_editor(request):
    """Retorna True se o usuário atual pode criar/editar atividades."""
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


@login_required
def lista_atividades(request):
    """Lista atividades com busca textual e filtros por instância, formato, tipo e status."""
    busca = request.GET.get('busca', '').strip()
    instancia_id = request.GET.get('instancia', '')
    formato = request.GET.get('formato', '')
    tipo = request.GET.get('tipo', '')
    status = request.GET.get('status', '')

    atividades = Atividade.objects.select_related('instancia')
    if busca:
        atividades = atividades.filter(
            Q(titulo__icontains=busca) | Q(instancia__nome__icontains=busca)
            | Q(pauta_resumo__icontains=busca) | Q(ata_resumo__icontains=busca)
        )
    if instancia_id:
        atividades = atividades.filter(instancia_id=instancia_id)
    if formato:
        atividades = atividades.filter(formato=formato)
    if tipo:
        atividades = atividades.filter(tipo_calendario=tipo)
    if status:
        atividades = atividades.filter(status=status)

    # KPIs do header
    total = Atividade.objects.count()
    realizadas = Atividade.objects.filter(status=Atividade.Status.REALIZADA).count()
    agendadas = Atividade.objects.filter(status=Atividade.Status.AGENDADA).count()
    com_ata = Atividade.objects.filter(possui_ata=True).count()

    contexto = {
        'atividades': atividades,
        'busca': busca,
        'instancia_filtro': instancia_id, 'instancias': Instancia.objects.order_by('nome'),
        'formato_filtro': formato, 'formatos': Atividade.Formato.choices,
        'tipo_filtro': tipo, 'tipos': Atividade.TipoCalendario.choices,
        'status_filtro': status, 'status_choices': Atividade.Status.choices,
        'eh_editor': _eh_editor(request),
        'header_icone': 'calendar-clock', 'header_cor': 'teal',
        'header_titulo': 'Atividades das Instâncias',
        'header_descricao': 'Reuniões e encontros vinculados a um Espaço de Diálogo. Cada atividade pode ter pauta, ata e lista de presença registradas.',
        'header_kpis': [
            {'label': 'atividades', 'valor': total, 'cor': 'gray'},
            {'label': 'realizadas', 'valor': realizadas, 'cor': 'emerald'},
            {'label': 'agendadas', 'valor': agendadas, 'cor': 'blue'},
            {'label': 'com ata', 'valor': com_ata, 'cor': 'teal'},
        ],
    }
    template = 'atividades/parciais/lista_atividades_tabela.html' if request.headers.get('HX-Request') else 'atividades/lista_atividades.html'
    return render(request, template, contexto)


@login_required
def detalhe_atividade(request, pk):
    """Detalhe da atividade: representantes esperados da instância (com municípios) e documentos."""
    atividade = get_object_or_404(Atividade.objects.select_related('instancia'), pk=pk)
    representacoes_qs = atividade.instancia.representacoes.filter(vigente=True).select_related('pessoa')
    participantes_esperados = []
    for rep in representacoes_qs:
        vinculo = rep.pessoa.vinculos.filter(vigente=True).select_related('municipio').first()
        participantes_esperados.append({
            'pessoa': rep.pessoa,
            'funcao': rep.get_funcao_display(),
            'municipio': vinculo.municipio if vinculo else None,
        })
    presencas = atividade.presencas.select_related('pessoa', 'municipio').order_by('pessoa__nome')
    contexto = {
        'atividade': atividade,
        'participantes_esperados': participantes_esperados,
        'documentos': atividade.documentos.all()[:10],
        'presencas': presencas,
        'historico': historico_de(atividade),
        'eh_editor': _eh_editor(request),
    }
    return render(request, 'atividades/detalhe_atividade.html', contexto)


@login_required
def criar_atividade(request):
    """Formulário de criação de atividade — restrito a editores."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para criar atividades.')
        return redirect('atividades:lista_atividades')
    if request.method == 'POST':
        form = AtividadeForm(request.POST)
        if form.is_valid():
            atividade = form.save()
            registrar_criacao(request.user, atividade)
            messages.success(request, 'Atividade registrada.')
            return redirect('atividades:lista_atividades')
    else:
        form = AtividadeForm()
    return render(request, 'atividades/form_atividade.html', {'form': form, 'atividade': None})


@login_required
def ata_pdf(request, pk):
    """Gera ata automatica em PDF a partir dos dados estruturados da atividade.

    Concatena: cabecalho institucional, pauta_resumo, lista de presencas,
    ata_resumo e documentos vinculados. Substitui processo manual de digitar
    ata em Word.
    """
    from io import BytesIO

    from django.http import HttpResponse
    from xhtml2pdf import pisa

    atividade = get_object_or_404(Atividade.objects.select_related('instancia'), pk=pk)
    presencas = atividade.presencas.select_related('pessoa', 'municipio').order_by('pessoa__nome')
    documentos = atividade.documentos.all()
    html = render(request, 'atividades/ata_pdf.html', {
        'atividade': atividade, 'presencas': presencas, 'documentos': documentos,
    }).content.decode('utf-8')

    pdf_buffer = BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)
    pdf_buffer.seek(0)
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ata-{atividade.pk}.pdf"'
    return response


@login_required
def editar_atividade(request, pk):
    """Formulário de edição de atividade — restrito a editores."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para editar atividades.')
        return redirect('atividades:lista_atividades')
    atividade = get_object_or_404(Atividade, pk=pk)
    if request.method == 'POST':
        form = AtividadeForm(request.POST, instance=atividade)
        if form.is_valid():
            alteracoes = detectar_alteracoes(atividade, form.cleaned_data)
            form.save()
            registrar_edicao(request.user, atividade, alteracoes)
            messages.success(request, 'Atividade atualizada.')
            return redirect('atividades:lista_atividades')
    else:
        form = AtividadeForm(instance=atividade)
    return render(request, 'atividades/form_atividade.html', {'form': form, 'atividade': atividade})
