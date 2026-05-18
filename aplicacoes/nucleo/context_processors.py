"""Context processors do núcleo — injetam dados de perfil em todos os templates."""

from aplicacoes.nucleo.servicos.permissoes import eh_editor as _eh_editor


def perfil_usuario(request):
    """Injeta ``eh_editor`` e ``permissoes`` no contexto global.

    ``permissoes`` é dict ``{slug: bool}`` com todas as permissões disponíveis,
    permitindo templates conditional via ``{% if permissoes.pode_importar_ibge %}``.
    """
    if not request.user.is_authenticated:
        return {'eh_editor': False, 'permissoes': {}}

    from aplicacoes.nucleo.models import Perfil
    permissoes = {}
    perfil = getattr(request.user, 'perfil', None)
    superusuario = request.user.is_superuser
    for slug, _ in Perfil.PERMISSOES_DISPONIVEIS:
        permissoes[slug] = superusuario or (perfil.pode(slug) if perfil else False)

    return {
        'eh_editor': _eh_editor(request),
        'permissoes': permissoes,
    }
