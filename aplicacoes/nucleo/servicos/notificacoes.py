"""Servico de notificacoes in-app — agrega alertas de varias fontes do sistema.

Retorna uma lista achatada e ordenada por urgencia. Sem persistencia: cada
chamada recalcula, leve o suficiente para rodar a cada 60s via HTMX polling.
"""

from datetime import date, timedelta

from django.urls import reverse


def listar_notificacoes(usuario, limite=10):
    """Coleta alertas relevantes para o usuario.

    Args:
        usuario: instancia de User logado (atualmente ignorado — todos veem todas).
        limite: total maximo de notificacoes retornadas.

    Returns:
        Lista de dicts ``{tipo, titulo, descricao, icone, cor, url, prioridade}``.
        ``prioridade`` numerica (1=critica, 3=info) usada para ordenacao.
    """
    from aplicacoes.adimplencia.models import Adimplencia
    from aplicacoes.cadastro.models import Pessoa
    from aplicacoes.eventos.models import Evento

    hoje = date.today()
    notificacoes = []

    # 1. Eventos nos proximos 7 dias
    eventos_proximos = (
        Evento.objects
        .filter(data_inicio__gte=hoje, data_inicio__lte=hoje + timedelta(days=7))
        .order_by('data_inicio')[:5]
    )
    for ev in eventos_proximos:
        dias = (ev.data_inicio - hoje).days
        notificacoes.append({
            'tipo': 'evento',
            'titulo': ev.titulo,
            'descricao': f'Em {dias} dia{"s" if dias != 1 else ""} · {ev.get_tipo_display()}',
            'icone': 'calendar-days',
            'cor': 'sky',
            'url': reverse('eventos:detalhe_evento', args=[ev.pk]),
            'prioridade': 2 if dias <= 1 else 3,
        })

    # 2. Adimplencias inadimplentes no ano corrente
    inadimplentes = (
        Adimplencia.objects
        .filter(ano_referencia=hoje.year, status='inadimplente')
        .select_related('municipio')
        .order_by('-valor_devido')[:3]
    )
    for ad in inadimplentes:
        notificacoes.append({
            'tipo': 'adimplencia',
            'titulo': f'{ad.municipio.nome}/{ad.municipio.uf} inadimplente',
            'descricao': f'R$ {ad.valor_devido:,.0f} devido — {ad.ano_referencia}'.replace(',', '.'),
            'icone': 'alert-triangle',
            'cor': 'red',
            'url': reverse('cadastro:detalhe_municipio', args=[ad.municipio.pk]),
            'prioridade': 1,
        })

    # 3. Mandatos terminando nos proximos 90 dias
    fim_em_90d = hoje + timedelta(days=90)
    mandatos = (
        Pessoa.objects
        .filter(ativo=True, mandato_fim__gte=hoje, mandato_fim__lte=fim_em_90d)
        .order_by('mandato_fim')[:3]
    )
    for p in mandatos:
        dias = (p.mandato_fim - hoje).days
        notificacoes.append({
            'tipo': 'mandato',
            'titulo': f'Mandato de {p.nome} termina em {dias} dia{"s" if dias != 1 else ""}',
            'descricao': p.cargo or p.get_tipo_display(),
            'icone': 'clock',
            'cor': 'amber',
            'url': reverse('cadastro:detalhe_pessoa', args=[p.pk]),
            'prioridade': 2 if dias <= 30 else 3,
        })

    # Ordena por prioridade (asc) e limita
    notificacoes.sort(key=lambda n: n['prioridade'])
    return notificacoes[:limite]
