"""Context processors do núcleo — injetam dados de perfil em todos os templates."""


def perfil_usuario(request):
    """Injeta ``eh_editor`` no contexto global para controle de permissão nos templates."""
    if request.user.is_authenticated:
        eh_editor = request.user.is_superuser
        if not eh_editor:
            try:
                eh_editor = request.user.perfil.eh_editor
            except Exception:
                eh_editor = False
        return {'eh_editor': eh_editor}
    return {'eh_editor': False}
