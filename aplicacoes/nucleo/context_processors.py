def perfil_usuario(request):
    """Disponibiliza informacoes de perfil em todos os templates."""
    if request.user.is_authenticated:
        eh_editor = request.user.is_superuser
        if not eh_editor:
            try:
                eh_editor = request.user.perfil.eh_editor
            except Exception:
                eh_editor = False
        return {'eh_editor': eh_editor}
    return {'eh_editor': False}
