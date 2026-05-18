"""Índice FNP composto — combina 4 sub-índices em uma nota única 0-100.

Substitui a leitura unidimensional do engajamento por um indicador que
reflete TODAS as dimensoes do relacionamento município ↔ FNP:

- engajamento  (40%)  pontuacao_normalizada do bienio atual
- adimplencia  (25%)  100 se adimplente, 50 se parcial, 0 se inadimplente
- participacao (20%)  numero de participacoes confirmadas no ano (clamp 0-100)
- presenca     (15%)  presencas confirmadas em atividades / total esperado

Pesos podem ser ajustados via constantes abaixo (futuro: model proprio).
Sem persistencia — recalcula sob demanda. Quando houver volume,
materializa em ``IndiceFNP`` model.
"""

from datetime import date

from django.db.models import Avg

PESOS = {
    'engajamento':  0.40,
    'adimplencia':  0.25,
    'participacao': 0.20,
    'presenca':     0.15,
}

# Patamar de "100%" de participação anual — calibrado para a meta FNP.
META_PARTICIPACOES_ANO = 12
META_PRESENCAS_ANO = 24


def _sub_adimplencia(municipio):
    """0-100 baseado no status de adimplência do ano atual."""
    from aplicacoes.adimplencia.models import Adimplencia
    ad = Adimplencia.objects.filter(
        municipio=municipio, ano_referencia=date.today().year,
    ).first()
    if not ad:
        return 0
    return {'adimplente': 100, 'parcial': 50, 'inadimplente': 0, 'isento': 80}.get(ad.status, 0)


def _sub_engajamento(municipio):
    """0-100 direto do Engajamento.pontuacao_normalizada do biênio."""
    eng = municipio.engajamentos.order_by('-bienio').first()
    return eng.pontuacao_normalizada if eng else 0


def _sub_participacao(municipio):
    """0-100 baseado em participações confirmadas no ano atual."""
    from aplicacoes.eventos.models import Participacao
    ano = date.today().year
    n = Participacao.objects.filter(
        municipio=municipio, confirmado=True,
        evento__data_inicio__year=ano,
    ).count()
    return min(100, int(n / META_PARTICIPACOES_ANO * 100))


def _sub_presenca(municipio):
    """0-100 baseado em presenças confirmadas em atividades."""
    from aplicacoes.presenca.models import Presenca
    ano = date.today().year
    n = Presenca.objects.filter(
        municipio=municipio, status='presente',
        criado_em__year=ano,
    ).count()
    return min(100, int(n / META_PRESENCAS_ANO * 100))


def calcular_indice(municipio):
    """Retorna dict com as 4 sub-notas + nota geral ponderada.

    Returns:
        ``{nota_geral, engajamento, adimplencia, participacao, presenca,
        nivel}`` com nota_geral arredondada e nivel categorizado.
    """
    eng = _sub_engajamento(municipio)
    adim = _sub_adimplencia(municipio)
    part = _sub_participacao(municipio)
    pres = _sub_presenca(municipio)

    geral = round(
        eng * PESOS['engajamento']
        + adim * PESOS['adimplencia']
        + part * PESOS['participacao']
        + pres * PESOS['presenca']
    )

    if geral >= 80:
        nivel = 'destaque'
    elif geral >= 60:
        nivel = 'consolidado'
    elif geral >= 40:
        nivel = 'em_construcao'
    else:
        nivel = 'critico'

    return {
        'nota_geral': geral,
        'engajamento': eng,
        'adimplencia': adim,
        'participacao': part,
        'presenca': pres,
        'nivel': nivel,
        'nivel_label': {
            'destaque': 'Destaque',
            'consolidado': 'Consolidado',
            'em_construcao': 'Em construção',
            'critico': 'Crítico',
        }[nivel],
    }


def ranking_top(limite=20, regiao=None, uf=None):
    """Ranking dos top N municípios por Índice FNP.

    Calculado em memória — fine pra <1k municípios. Acima disso, materializar.
    """
    from aplicacoes.cadastro.models import Municipio
    qs = Municipio.objects.all()
    if regiao:
        qs = qs.filter(regiao=regiao)
    if uf:
        qs = qs.filter(uf=uf)
    qs = qs.filter(associado_fnp=True)  # só faz sentido para associados
    municipios = list(qs)

    rankeados = [
        {'municipio': m, **calcular_indice(m)}
        for m in municipios
    ]
    rankeados.sort(key=lambda x: x['nota_geral'], reverse=True)
    return rankeados[:limite]
