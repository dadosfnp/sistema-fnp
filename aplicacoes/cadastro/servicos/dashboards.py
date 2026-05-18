"""Serviços que montam contextos prontos para as views de detalhe.

Tira a lógica de agregação das views (que devem ser finas: receber request,
delegar pra serviço, renderizar). Mais testável e reutilizável (por exemplo,
a página de comparar municípios pode reaproveitar ``contexto_municipio``).
"""


def contexto_municipio(municipio):
    """Monta o contexto completo da página de detalhe do município.

    Args:
        municipio: Instância de Municipio.

    Returns:
        Dict com vinculos, adimplencias, engajamento e participações
        prontos para passar ao template ``cadastro/detalhe_municipio.html``.
    """
    return {
        'municipio': municipio,
        'vinculos': (
            municipio.vinculos.select_related('pessoa')
            .filter(vigente=True).order_by('papel')
        ),
        'adimplencias': municipio.adimplencias.order_by('-ano_referencia')[:5],
        'engajamento': municipio.engajamentos.first(),
        'participacoes': (
            municipio.participacoes
            .select_related('pessoa', 'evento')
            .order_by('-evento__data_inicio')[:20]
        ),
    }


def contexto_pessoa(pessoa):
    """Monta o contexto completo da página de detalhe da pessoa."""
    return {
        'pessoa': pessoa,
        'vinculos': (
            pessoa.vinculos.select_related('municipio').order_by('-vigente', '-inicio_mandato')
            if hasattr(pessoa, 'vinculos') else []
        ),
        'participacoes': (
            pessoa.participacoes.select_related('evento', 'municipio')
            .order_by('-evento__data_inicio')[:10]
            if hasattr(pessoa, 'participacoes') else []
        ),
    }
