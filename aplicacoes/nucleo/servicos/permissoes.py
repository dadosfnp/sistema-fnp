"""Helpers de permissão centralizados.

Substitui o ``_eh_editor`` duplicado em cada views.py. Cada view importa
``pode`` ou ``eh_editor`` daqui e ganha checagem granular sem repetir try/except.
"""


def eh_editor(request):
    """Compatível com o ``_eh_editor`` antigo — True se pode editar."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.perfil.eh_editor
    except Exception:
        return False


def pode(request, permissao):
    """Granular: verifica permissão específica (ex: 'pode_importar_ibge')."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.perfil.pode(permissao)
    except Exception:
        return False
