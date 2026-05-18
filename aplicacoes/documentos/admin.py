"""Admin Unfold para Documento universal.

Inclui também ``DocumentoGenericInline``, reutilizável dentro de qualquer
ModelAdmin para permitir gerenciar documentos de uma entidade pelo admin.
"""

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from unfold.admin import ModelAdmin

from .models import Documento


class DocumentoGenericInline(GenericTabularInline):
    """Inline genérico de documentos — incluir em ModelAdmin de qualquer entidade.

    Exemplo: ``inlines = [DocumentoGenericInline]`` em ``InstanciaAdmin``.
    """
    model = Documento
    extra = 0
    fields = ['nome', 'tipo', 'arquivo', 'link_externo', 'descricao']
    ct_field = 'content_type'
    ct_fk_field = 'object_id'


@admin.register(Documento)
class DocumentoAdmin(ModelAdmin):
    """Admin de Documento centralizado, útil para auditoria geral."""
    list_display = ['nome', 'tipo', 'content_type', 'criado_em', 'enviado_por']
    list_filter = ['tipo', 'content_type', 'criado_em']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['enviado_por', 'criado_em', 'atualizado_em']
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'tipo', 'descricao'),
        }),
        ('Arquivo', {
            'fields': ('arquivo', 'link_externo'),
        }),
        ('Vínculo', {
            'fields': ('content_type', 'object_id'),
            'description': 'Entidade dona do documento (Instância, Projeto, Missão etc.).',
        }),
        ('Auditoria', {
            'fields': ('enviado_por', 'criado_em', 'atualizado_em'),
        }),
    )

    def save_model(self, request, obj, form, change):
        """Registra automaticamente o usuário que está enviando o documento."""
        if not obj.enviado_por_id:
            obj.enviado_por = request.user
        super().save_model(request, obj, form, change)
