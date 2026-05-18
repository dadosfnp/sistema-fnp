"""Views de cadastro: CRUD de Pessoa e Município com controle de permissão."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from aplicacoes.cadastro.forms import MunicipioForm, PessoaForm
from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.cadastro.servicos.dashboards import contexto_municipio, contexto_pessoa
from aplicacoes.nucleo.servicos.auditoria import detectar_alteracoes, registrar_criacao, registrar_edicao


def _eh_editor(request):
    """Verifica se o usuário logado possui permissão de edição."""
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


@login_required
def lista_pessoas(request):
    """Lista pessoas com busca, filtro por tipo e paginação (50 por página).

    Aceita ``?exportar=csv`` para baixar a visao filtrada (sem paginacao).
    """
    busca = request.GET.get('busca', '').strip()
    tipo = request.GET.get('tipo', '')
    pessoas_qs = Pessoa.objects.filter(ativo=True).order_by('nome')
    if busca:
        pessoas_qs = pessoas_qs.filter(
            Q(nome__icontains=busca) | Q(cargo__icontains=busca) | Q(partido__icontains=busca)
        )
    if tipo:
        pessoas_qs = pessoas_qs.filter(tipo=tipo)

    if request.GET.get('exportar') == 'csv':
        from aplicacoes.nucleo.servicos.exportacao import exportar_csv
        return exportar_csv(
            nome_arquivo='pessoas-filtradas',
            cabecalho=['Nome', 'Tipo', 'Cargo', 'Partido', 'E-mail', 'Ativo'],
            linhas_iter=(
                [p.nome, p.get_tipo_display(), p.cargo, p.partido, p.email or '', 'Sim' if p.ativo else 'Nao']
                for p in pessoas_qs
            ),
        )

    paginator = Paginator(pessoas_qs, 50)
    pagina = paginator.get_page(request.GET.get('pagina'))

    tipos = Pessoa.TipoPessoa.choices
    ctx = {
        'pessoas': pagina.object_list,
        'pagina': pagina,
        'total_resultados': paginator.count,
        'busca': busca, 'tipo': tipo, 'tipos': tipos,
    }
    template = 'cadastro/parciais/lista_pessoas_tabela.html' if request.headers.get('HX-Request') else 'cadastro/lista_pessoas.html'
    return render(request, template, ctx)


@login_required
def detalhe_pessoa(request, pk):
    """Exibe detalhes de uma pessoa — delega monta-contexto ao serviço de dashboard."""
    pessoa = get_object_or_404(Pessoa, pk=pk)
    return render(request, 'cadastro/detalhe_pessoa.html', contexto_pessoa(pessoa))


@login_required
def editar_pessoa(request, pk):
    """Formulário de edição de pessoa com auditoria."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para editar.')
        return redirect('cadastro:detalhe_pessoa', pk=pk)
    pessoa = get_object_or_404(Pessoa, pk=pk)
    if request.method == 'POST':
        form = PessoaForm(request.POST, request.FILES, instance=pessoa)
        if form.is_valid():
            alteracoes = detectar_alteracoes(pessoa, form.cleaned_data)
            form.save()
            registrar_edicao(request.user, pessoa, alteracoes)
            messages.success(request, f'{pessoa.nome} atualizado com sucesso.')
            return redirect('cadastro:detalhe_pessoa', pk=pk)
    else:
        form = PessoaForm(instance=pessoa)
    return render(request, 'cadastro/form_pessoa.html', {'form': form, 'pessoa': pessoa})


@login_required
def criar_pessoa(request):
    """Formulário de criação de pessoa com auditoria."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para cadastrar.')
        return redirect('cadastro:lista_pessoas')
    if request.method == 'POST':
        form = PessoaForm(request.POST, request.FILES)
        if form.is_valid():
            pessoa = form.save()
            registrar_criacao(request.user, pessoa)
            messages.success(request, f'{pessoa.nome} cadastrado com sucesso.')
            return redirect('cadastro:detalhe_pessoa', pk=pessoa.pk)
    else:
        form = PessoaForm()
    return render(request, 'cadastro/form_pessoa.html', {'form': form, 'pessoa': None})


@login_required
def lista_municipios(request):
    """Lista municípios com busca, filtros por UF/região/adimplência e paginação (50/pg)."""
    busca = request.GET.get('busca', '').strip()
    uf = request.GET.get('uf', '')
    regiao = request.GET.get('regiao', '')
    adimplencia = request.GET.get('adimplencia', '')
    municipios_qs = Municipio.objects.all().order_by('nome')
    if busca:
        municipios_qs = municipios_qs.filter(Q(nome__icontains=busca) | Q(uf__icontains=busca))
    if uf:
        municipios_qs = municipios_qs.filter(uf=uf)
    if regiao:
        municipios_qs = municipios_qs.filter(regiao=regiao)
    if adimplencia:
        municipios_qs = municipios_qs.filter(
            adimplencias__status=adimplencia, adimplencias__ano_referencia=2026,
        ).distinct()

    if request.GET.get('exportar') == 'csv':
        from aplicacoes.nucleo.servicos.exportacao import exportar_csv
        return exportar_csv(
            nome_arquivo='municipios-filtrados',
            cabecalho=['Nome', 'UF', 'Regiao', 'Populacao', 'Capital', 'Associado FNP', 'Adimplencia atual'],
            linhas_iter=(
                [m.nome, m.uf, m.get_regiao_display() or '', m.populacao,
                 'Sim' if m.eh_capital else 'Nao',
                 'Sim' if m.associado_fnp else 'Nao',
                 m.adimplencia_atual or '']
                for m in municipios_qs
            ),
        )

    paginator = Paginator(municipios_qs, 50)
    pagina = paginator.get_page(request.GET.get('pagina'))

    ufs = Municipio.objects.values_list('uf', flat=True).distinct().order_by('uf')
    regioes = Municipio.Regiao.choices
    ctx = {
        'municipios': pagina.object_list,
        'pagina': pagina,
        'total_resultados': paginator.count,
        'busca': busca,
        'uf': uf, 'ufs': ufs, 'regiao': regiao, 'regioes': regioes,
        'adimplencia_filtro': adimplencia,
    }
    template = 'cadastro/parciais/lista_municipios_tabela.html' if request.headers.get('HX-Request') else 'cadastro/lista_municipios.html'
    return render(request, template, ctx)


@login_required
def detalhe_municipio(request, pk):
    """Exibe detalhes do município — delega monta-contexto ao serviço de dashboard."""
    municipio = get_object_or_404(Municipio, pk=pk)
    return render(request, 'cadastro/detalhe_municipio.html', contexto_municipio(municipio))


@login_required
def editar_municipio(request, pk):
    """Formulário de edição de município com auditoria."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para editar.')
        return redirect('cadastro:detalhe_municipio', pk=pk)
    municipio = get_object_or_404(Municipio, pk=pk)
    if request.method == 'POST':
        form = MunicipioForm(request.POST, request.FILES, instance=municipio)
        if form.is_valid():
            alteracoes = detectar_alteracoes(municipio, form.cleaned_data)
            form.save()
            registrar_edicao(request.user, municipio, alteracoes)
            messages.success(request, f'{municipio.nome} atualizado com sucesso.')
            return redirect('cadastro:detalhe_municipio', pk=pk)
    else:
        form = MunicipioForm(instance=municipio)
    return render(request, 'cadastro/form_municipio.html', {'form': form, 'municipio': municipio})


@login_required
def criar_municipio(request):
    """Formulário de criação de município com auditoria."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para cadastrar.')
        return redirect('cadastro:lista_municipios')
    if request.method == 'POST':
        form = MunicipioForm(request.POST, request.FILES)
        if form.is_valid():
            municipio = form.save()
            registrar_criacao(request.user, municipio)
            messages.success(request, f'{municipio.nome} cadastrado com sucesso.')
            return redirect('cadastro:detalhe_municipio', pk=municipio.pk)
    else:
        form = MunicipioForm()
    return render(request, 'cadastro/form_municipio.html', {'form': form, 'municipio': None})
