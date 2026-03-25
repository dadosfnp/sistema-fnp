"""Views do núcleo: autenticação (login/logout) e dashboard inicial."""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.engajamento.models import Engajamento
from aplicacoes.eventos.models import Evento


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
        'total_associados': Municipio.objects.filter(associado_fnp=True).count(),
        'total_eventos': Evento.objects.count(),
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
