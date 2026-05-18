"""Gerador de narrativa textual para o painel de relatorios.

Substitui graficos isolados por frases acionaveis tipo
"Adimplencia cresceu 12 pp no Nordeste em 2026". Modelo: templates de frase
parametrizados — funciona offline, sem LLM. Pode evoluir para Claude/GPT
no futuro mantendo a mesma interface.
"""

from datetime import date

from django.db.models import Avg, Count


def _percent(parte, total):
    if not total:
        return 0
    return round(parte / total * 100, 1)


def gerar_insights():
    """Retorna lista de dicts ``{tipo, texto, severidade}`` para exibicao.

    ``severidade`` pode ser: positivo, neutro, atencao, critico.
    Cada insight é uma frase pronta para o painel.
    """
    from aplicacoes.adimplencia.models import Adimplencia
    from aplicacoes.cadastro.models import Municipio
    from aplicacoes.engajamento.models import Engajamento
    from aplicacoes.eventos.models import Participacao

    insights = []
    ano_atual = date.today().year
    ano_anterior = ano_atual - 1

    # --- 1. Variacao de adimplencia ano contra ano ---
    adim_atual = Adimplencia.objects.filter(ano_referencia=ano_atual)
    adim_anterior = Adimplencia.objects.filter(ano_referencia=ano_anterior)
    total_atual = adim_atual.count()
    if total_atual:
        pct_adimplentes_atual = _percent(adim_atual.filter(status='adimplente').count(), total_atual)
        total_anterior = adim_anterior.count()
        if total_anterior:
            pct_adimplentes_anterior = _percent(adim_anterior.filter(status='adimplente').count(), total_anterior)
            delta = round(pct_adimplentes_atual - pct_adimplentes_anterior, 1)
            if abs(delta) >= 2:
                direcao = 'subiu' if delta > 0 else 'caiu'
                sev = 'positivo' if delta > 0 else 'atencao'
                insights.append({
                    'tipo': 'adimplencia_yoy',
                    'texto': f'Adimplência {direcao} {abs(delta)} pontos percentuais entre {ano_anterior} e {ano_atual} — hoje {pct_adimplentes_atual}% dos {total_atual} municípios registrados estão em dia.',
                    'severidade': sev,
                })
            else:
                insights.append({
                    'tipo': 'adimplencia_estavel',
                    'texto': f'Adimplência estável: {pct_adimplentes_atual}% adimplentes em {ano_atual} ({total_atual} municípios), variação inferior a 2 pp vs {ano_anterior}.',
                    'severidade': 'neutro',
                })
        else:
            insights.append({
                'tipo': 'adimplencia_atual',
                'texto': f'{pct_adimplentes_atual}% dos {total_atual} municípios com registro estão adimplentes em {ano_atual}.',
                'severidade': 'neutro',
            })

    # --- 2. Regiao com mais inadimplencia ---
    if total_atual:
        por_regiao = (
            Adimplencia.objects.filter(ano_referencia=ano_atual, status='inadimplente')
            .values('municipio__regiao')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        if por_regiao:
            top = por_regiao[0]
            regiao_nome = dict(Municipio.Regiao.choices).get(top['municipio__regiao'], top['municipio__regiao'])
            if top['total'] >= 2:
                insights.append({
                    'tipo': 'regiao_critica',
                    'texto': f'{regiao_nome} concentra a maior quantidade de inadimplentes em {ano_atual}: {top["total"]} municípios. Vale priorizar contato comercial.',
                    'severidade': 'critico',
                })

    # --- 3. Engajamento medio + top 1 ---
    eng_qs = Engajamento.objects.all()
    if eng_qs.exists():
        media = round(eng_qs.aggregate(m=Avg('pontuacao_normalizada'))['m'] or 0, 1)
        top = eng_qs.order_by('-pontuacao_normalizada').first()
        sev = 'positivo' if media >= 60 else ('atencao' if media >= 40 else 'critico')
        insights.append({
            'tipo': 'engajamento_geral',
            'texto': f'Engajamento médio do biênio: {media}/100. Liderança: {top.municipio.nome}/{top.municipio.uf} com {top.pontuacao_normalizada} pontos.',
            'severidade': sev,
        })

    # --- 4. Cobertura: % de associados com registro de engajamento ---
    total_municipios = Municipio.objects.count()
    total_associados = Municipio.objects.filter(associado_fnp=True).count()
    if total_associados:
        com_engajamento = (
            Engajamento.objects.values('municipio_id').distinct().count()
        )
        pct_cobertos = _percent(com_engajamento, total_associados)
        if pct_cobertos < 80:
            insights.append({
                'tipo': 'cobertura_baixa',
                'texto': f'Apenas {pct_cobertos}% dos {total_associados} municípios associados têm engajamento calculado. {total_associados - com_engajamento} municípios precisam de atualização de participações.',
                'severidade': 'atencao',
            })
        else:
            insights.append({
                'tipo': 'cobertura_alta',
                'texto': f'{pct_cobertos}% dos municípios associados têm engajamento calculado — cobertura saudável.',
                'severidade': 'positivo',
            })

    # --- 5. Atividade do biênio ---
    part_confirmadas = Participacao.objects.filter(confirmado=True).count()
    if part_confirmadas:
        insights.append({
            'tipo': 'participacoes',
            'texto': f'{part_confirmadas} participações confirmadas em eventos da FNP até hoje. Cada participação alimenta o ranking de engajamento automaticamente.',
            'severidade': 'neutro',
        })

    return insights
