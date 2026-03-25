"""Configuração do admin para User (com Perfil inline) e LogAlteracao."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin

from aplicacoes.nucleo.models import LogAlteracao, Perfil


class PerfilInline(admin.StackedInline):
    """Inline para editar o Perfil de acesso diretamente no formulário do User."""
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil de acesso'


class UserAdmin(BaseUserAdmin):
    """Admin customizado do User com inline de Perfil e coluna de tipo de acesso."""
    inlines = [PerfilInline]
    list_display = ['username', 'get_full_name', 'email', 'get_perfil', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff', 'perfil__tipo']

    @admin.display(description='Perfil')
    def get_perfil(self, obj):
        try:
            return obj.perfil.get_tipo_display()
        except Perfil.DoesNotExist:
            return '—'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(LogAlteracao)
class LogAlteracaoAdmin(ModelAdmin):
    """Admin somente-leitura para visualização dos logs de auditoria."""
    list_display = ['data', 'usuario', 'acao', 'modelo', 'objeto_repr']
    list_filter = ['acao', 'modelo', 'data']
    search_fields = ['objeto_repr', 'usuario__username']
    readonly_fields = ['usuario', 'acao', 'modelo', 'objeto_id', 'objeto_repr', 'campos_alterados', 'data']
    date_hierarchy = 'data'

    def has_add_permission(self, request):
        """Logs são criados apenas programaticamente."""
        return False

    def has_change_permission(self, request, obj=None):
        """Logs são imutáveis — edição desabilitada."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Apenas superusuários podem excluir logs."""
        return request.user.is_superuser
