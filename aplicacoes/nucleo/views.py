"""Views do núcleo: autenticação (login/logout), dashboard inicial e busca global."""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.atividades.models import Atividade
from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.engajamento.models import Engajamento
from aplicacoes.eventos.models import Evento
from aplicacoes.instancias.models import Instancia
from aplicacoes.missoes.models import Missao
from aplicacoes.projetos.models import Projeto


def entrar(request):
    """Processa login via POST (usuario/senha) e renderiza tela de entrada."""
    erro = ''
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        senha = request.POST.get('senha', '')
        user = authenticate(request, username=usuario, password=senha)
        if user is not None:
            login(request, user)
            proximo = request.GET.get('next', '/')
            return redirect(proximo)
        else:
            erro = 'Usuario ou senha incorretos.'
    return render(request, 'nucleo/entrar.html', {'erro': erro})


@login_required
def inicio(request):
    """Renderiza o dashboard principal com indicadores agregados do sistema."""
    contexto = {
        'total_pessoas': Pessoa.objects.filter(ativo=True).count(),
        'total_municipios': Municipio.objects.count(),
        'total_eventos': Evento.objects.count(),
        'total_instancias': Instancia.objects.count(),
        'total_projetos': Projeto.objects.count(),
        'total_missoes': Missao.objects.count(),
        'total_atividades': Atividade.objects.count(),
        'total_adimplentes': Adimplencia.objects.filter(ano_referencia=2026, status='adimplente').count(),
        'total_inadimplentes': Adimplencia.objects.filter(ano_referencia=2026, status='inadimplente').count(),
        'eventos_recentes': Evento.objects.order_by('-data_inicio')[:5],
        'top_engajamento': Engajamento.objects.select_related('municipio').order_by('-pontuacao_bruta')[:5],
    }
    return render(request, 'nucleo/inicio.html', contexto)


def sair(request):
    """Encerra a sessão do usuário e redireciona para a tela de login."""
    logout(request)
    return redirect('nucleo:entrar')


@login_required
def filtros_salvos_listar(request):
    """Lista filtros salvos do usuário no escopo informado (URL name)."""
    from aplicacoes.nucleo.models import FiltroSalvo
    escopo = request.GET.get('escopo', '')
    filtros = FiltroSalvo.objects.filter(usuario=request.user, escopo=escopo).order_by('nome')
    return JsonResponse({
        'filtros': [
            {'id': f.id, 'nome': f.nome, 'parametros': f.parametros}
            for f in filtros
        ],
    })


@login_required
def filtros_salvos_criar(request):
    """Salva um novo filtro nomeado vinculado ao escopo + parâmetros atuais."""
    from aplicacoes.nucleo.models import FiltroSalvo
    if request.method != 'POST':
        return JsonResponse({'erro': 'use POST'}, status=405)
    escopo = (request.POST.get('escopo') or '').strip()
    nome = (request.POST.get('nome') or '').strip()
    parametros = (request.POST.get('parametros') or '').strip()
    if not escopo or not nome:
        return JsonResponse({'erro': 'escopo e nome obrigatorios'}, status=400)
    filtro, criado = FiltroSalvo.objects.update_or_create(
        usuario=request.user, escopo=escopo, nome=nome,
        defaults={'parametros': parametros},
    )
    return JsonResponse({'id': filtro.id, 'nome': filtro.nome, 'criado': criado})


@login_required
def filtros_salvos_remover(request, pk):
    """Remove um filtro salvo do usuário."""
    from aplicacoes.nucleo.models import FiltroSalvo
    if request.method != 'POST':
        return JsonResponse({'erro': 'use POST'}, status=405)
    FiltroSalvo.objects.filter(pk=pk, usuario=request.user).delete()
    return JsonResponse({'ok': True})


@login_required
def notificacoes_dropdown(request):
    """Renderiza o dropdown HTMX de notificacoes (parcial chamado por polling)."""
    from aplicacoes.nucleo.servicos.notificacoes import listar_notificacoes
    notificacoes = listar_notificacoes(request.user)
    return render(request, 'nucleo/parciais/notificacoes.html', {
        'notificacoes': notificacoes,
        'total': len(notificacoes),
    })


@login_required
def portal_prefeito(request):
    """Dashboard do portal externo — visivel apenas para perfis tipo='prefeito'.

    Mostra metricas do municipio vinculado ao perfil. Acesso a outros
    municipios e bloqueado pelo middleware ``IsolarPortalPrefeitoMiddleware``.
    """
    from aplicacoes.cadastro.models import Municipio
    from aplicacoes.engajamento.servicos.indice_fnp import calcular_indice

    perfil = getattr(request.user, 'perfil', None)
    if not perfil or not perfil.municipio_vinculado:
        # Admin ou perfil sem municipio — mostra mensagem amigavel
        return render(request, 'portal/sem_vinculo.html')

    municipio = perfil.municipio_vinculado
    indice = calcular_indice(municipio)

    # Coleta dados visiveis para o prefeito do proprio municipio
    vinculos = municipio.vinculos.filter(vigente=True).select_related('pessoa')
    engajamento = municipio.engajamentos.order_by('-bienio').first()
    adimplencia = municipio.adimplencias.order_by('-ano_referencia').first()
    participacoes = municipio.participacoes.select_related('pessoa', 'evento').order_by('-evento__data_inicio')[:10]

    # Posicao no ranking nacional
    posicao = None
    if engajamento:
        from aplicacoes.engajamento.models import Engajamento
        posicao = (
            Engajamento.objects.filter(pontuacao_normalizada__gt=engajamento.pontuacao_normalizada).count() + 1
        )

    return render(request, 'portal/dashboard.html', {
        'municipio': municipio,
        'indice': indice,
        'vinculos': vinculos,
        'engajamento': engajamento,
        'adimplencia': adimplencia,
        'participacoes': participacoes,
        'posicao_ranking': posicao,
    })


@login_required
def busca_global(request):
    """Endpoint JSON de busca global usado pela paleta de comandos (Ctrl+K).

    Aceita ``q`` via GET e retorna até 5 hits por categoria com link de
    detalhe e ícone. Limita resultados para manter latência baixa.
    """
    termo = (request.GET.get('q') or '').strip()
    if len(termo) < 2:
        return JsonResponse({'resultados': []})

    resultados = []

    for p in Pessoa.objects.filter(nome__icontains=termo).only('id', 'nome', 'cargo')[:5]:
        resultados.append({
            'tipo': 'Pessoa', 'icone': 'user',
            'titulo': p.nome, 'subtitulo': p.cargo or '—',
            'url': reverse('cadastro:detalhe_pessoa', args=[p.pk]),
        })

    for m in Municipio.objects.filter(Q(nome__icontains=termo) | Q(uf__iexact=termo)).only('id', 'nome', 'uf', 'regiao')[:5]:
        resultados.append({
            'tipo': 'Município', 'icone': 'building-2',
            'titulo': f'{m.nome}/{m.uf}', 'subtitulo': m.get_regiao_display() or '—',
            'url': reverse('cadastro:detalhe_municipio', args=[m.pk]),
        })

    for inst in Instancia.objects.filter(nome__icontains=termo).only('id', 'nome', 'origem')[:5]:
        resultados.append({
            'tipo': 'Instância', 'icone': 'messages-square',
            'titulo': inst.nome, 'subtitulo': inst.get_origem_display() or '—',
            'url': reverse('instancias:detalhe_instancia', args=[inst.pk]),
        })

    for ev in Evento.objects.filter(titulo__icontains=termo).only('id', 'titulo', 'tipo', 'data_inicio')[:5]:
        resultados.append({
            'tipo': 'Evento', 'icone': 'calendar-days',
            'titulo': ev.titulo, 'subtitulo': f'{ev.get_tipo_display()} · {ev.data_inicio.strftime("%d/%m/%Y")}',
            'url': reverse('eventos:detalhe_evento', args=[ev.pk]),
        })

    for proj in Projeto.objects.filter(nome__icontains=termo).only('id', 'nome', 'status')[:3]:
        resultados.append({
            'tipo': 'Projeto', 'icone': 'clipboard-list',
            'titulo': proj.nome, 'subtitulo': proj.get_status_display() or '—',
            'url': reverse('projetos:detalhe_projeto', args=[proj.pk]),
        })

    for miss in Missao.objects.filter(titulo__icontains=termo).only('id', 'titulo', 'tipo', 'cidade')[:3]:
        resultados.append({
            'tipo': 'Missão', 'icone': 'plane-takeoff',
            'titulo': miss.titulo, 'subtitulo': f'{miss.get_tipo_display()} · {miss.cidade or "—"}',
            'url': reverse('missoes:detalhe_missao', args=[miss.pk]),
        })

    return JsonResponse({'resultados': resultados, 'total': len(resultados), 'termo': termo})
