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

    # 4. Padrao proativo: faltas consecutivas em atividades de uma mesma instancia.
    # Detecta pessoas com >= 3 status='ausente' ou 'justificada' nas ultimas
    # 5 atividades da mesma instancia. Sinal precoce de desengajamento.
    notificacoes.extend(_faltas_consecutivas(limite=3))

    # 5. Municipios cujo engajamento caiu mais de 15 pontos no bienio (placeholder
    # ate termos dois biennios — por ora flag "nivel inativo + associado")
    notificacoes.extend(_associados_inativos(limite=3))

    # Ordena por prioridade (asc) e limita
    notificacoes.sort(key=lambda n: n['prioridade'])
    return notificacoes[:limite]


def _faltas_consecutivas(limite=3):
    """Detecta pessoas que faltaram >= 3 das ultimas 5 atividades da instancia.

    Sinal proativo de desengajamento — algo que so emerge cruzando dados.
    """
    from collections import defaultdict

    from aplicacoes.atividades.models import Atividade
    from aplicacoes.instancias.models import Representacao
    from aplicacoes.presenca.models import Presenca

    alerts = []
    # Para cada instancia ativa, ve ultimas 5 atividades
    instancias_com_atividade = set(
        Atividade.objects.values_list('instancia_id', flat=True).distinct()
    )
    for inst_id in instancias_com_atividade:
        ultimas = list(
            Atividade.objects.filter(instancia_id=inst_id)
            .order_by('-data_reuniao')[:5]
        )
        if len(ultimas) < 3:
            continue
        ids_atividades = [a.id for a in ultimas]
        # Conta presencas/ausencias por pessoa nessas atividades
        presencas = Presenca.objects.filter(object_id__in=ids_atividades).values('pessoa_id', 'status')
        contagem = defaultdict(lambda: {'presente': 0, 'ausente_ou_just': 0})
        for p in presencas:
            if p['status'] == 'presente':
                contagem[p['pessoa_id']]['presente'] += 1
            elif p['status'] in ('ausente', 'justificada'):
                contagem[p['pessoa_id']]['ausente_ou_just'] += 1

        for pessoa_id, c in contagem.items():
            if c['ausente_ou_just'] >= 3:
                rep = Representacao.objects.filter(
                    pessoa_id=pessoa_id, instancia_id=inst_id, vigente=True,
                ).select_related('pessoa', 'instancia').first()
                if rep:
                    alerts.append({
                        'tipo': 'faltas_consecutivas',
                        'titulo': f'{rep.pessoa.nome} faltou {c["ausente_ou_just"]} das últimas {len(ultimas)} reuniões',
                        'descricao': f'Instância: {rep.instancia.nome}',
                        'icone': 'user-x',
                        'cor': 'red',
                        'url': reverse('instancias:detalhe_instancia', args=[rep.instancia.pk]),
                        'prioridade': 1,
                    })
                if len(alerts) >= limite:
                    return alerts
    return alerts


def _associados_inativos(limite=3):
    """Detecta municipios associados com engajamento 'inativo' — anomalia."""
    from aplicacoes.engajamento.models import Engajamento

    alerts = []
    inativos = (
        Engajamento.objects.filter(nivel='inativo', municipio__associado_fnp=True)
        .select_related('municipio')
        .order_by('-pontuacao_normalizada')[:limite]
    )
    for e in inativos:
        alerts.append({
            'tipo': 'associado_inativo',
            'titulo': f'{e.municipio.nome}/{e.municipio.uf} está associado mas inativo',
            'descricao': f'Pontuação atual: {e.pontuacao_normalizada}/100 no biênio {e.bienio}',
            'icone': 'alert-octagon',
            'cor': 'red',
            'url': reverse('cadastro:detalhe_municipio', args=[e.municipio.pk]),
            'prioridade': 1,
        })
    return alerts
