"""Views de cadastro: CRUD de Pessoa e Município com controle de permissão."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from aplicacoes.cadastro.forms import MunicipioForm, PessoaForm
from aplicacoes.cadastro.models import Municipio, Pessoa
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
    """Lista pessoas com busca e filtros por tipo e partido."""
    busca = request.GET.get('busca', '').strip()
    tipo = request.GET.get('tipo', '')
    pessoas = Pessoa.objects.filter(ativo=True).order_by('nome')
    if busca:
        pessoas = pessoas.filter(
            Q(nome__icontains=busca) | Q(cargo__icontains=busca) | Q(partido__icontains=busca)
        )
    if tipo:
        pessoas = pessoas.filter(tipo=tipo)
    tipos = Pessoa.TipoPessoa.choices
    ctx = {'pessoas': pessoas, 'busca': busca, 'tipo': tipo, 'tipos': tipos}
    template = 'cadastro/parciais/lista_pessoas_tabela.html' if request.headers.get('HX-Request') else 'cadastro/lista_pessoas.html'
    return render(request, template, ctx)


@login_required
def detalhe_pessoa(request, pk):
    """Exibe detalhes de uma pessoa com vínculos e participações."""
    pessoa = get_object_or_404(Pessoa, pk=pk)
    vinculos = pessoa.vinculos.select_related('municipio').order_by('-vigente', '-inicio_mandato')
    participacoes = pessoa.participacoes.select_related('evento', 'municipio').order_by('-evento__data_inicio')[:20]
    return render(request, 'cadastro/detalhe_pessoa.html', {
        'pessoa': pessoa, 'vinculos': vinculos, 'participacoes': participacoes,
    })


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
    """Lista municípios com busca e filtros por UF, região e associação."""
    busca = request.GET.get('busca', '').strip()
    uf = request.GET.get('uf', '')
    regiao = request.GET.get('regiao', '')
    associado = request.GET.get('associado', '')
    municipios = Municipio.objects.all().order_by('nome')
    if busca:
        municipios = municipios.filter(Q(nome__icontains=busca) | Q(uf__icontains=busca))
    if uf:
        municipios = municipios.filter(uf=uf)
    if regiao:
        municipios = municipios.filter(regiao=regiao)
    if associado:
        municipios = municipios.filter(associado_fnp=(associado == 'sim'))
    ufs = Municipio.objects.values_list('uf', flat=True).distinct().order_by('uf')
    regioes = Municipio.Regiao.choices
    ctx = {
        'municipios': municipios, 'busca': busca,
        'uf': uf, 'ufs': ufs, 'regiao': regiao, 'regioes': regioes, 'associado': associado,
    }
    template = 'cadastro/parciais/lista_municipios_tabela.html' if request.headers.get('HX-Request') else 'cadastro/lista_municipios.html'
    return render(request, template, ctx)


@login_required
def detalhe_municipio(request, pk):
    """Exibe detalhes do município com vínculos, adimplência, engajamento e participações."""
    municipio = get_object_or_404(Municipio, pk=pk)
    vinculos = municipio.vinculos.select_related('pessoa').filter(vigente=True).order_by('papel')
    adimplencias = municipio.adimplencias.order_by('-ano_referencia')[:5]
    engajamento = municipio.engajamentos.first()
    participacoes = municipio.participacoes.select_related('pessoa', 'evento').order_by('-evento__data_inicio')[:20]
    return render(request, 'cadastro/detalhe_municipio.html', {
        'municipio': municipio, 'vinculos': vinculos, 'adimplencias': adimplencias,
        'engajamento': engajamento, 'participacoes': participacoes,
    })


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
