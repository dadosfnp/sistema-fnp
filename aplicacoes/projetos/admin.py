"""Admin Unfold para Projetos."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from aplicacoes.documentos.admin import DocumentoGenericInline

from .models import Projeto


@admin.register(Projeto)
class ProjetoAdmin(ModelAdmin):
    """Admin de Projeto com fieldsets de identificação, prazos e financeiro."""
    list_display = ['nome', 'status', 'responsavel', 'data_inicio', 'data_fim_previsto', 'fonte_recurso']
    list_filter = ['status', 'fonte_recurso']
    search_fields = ['nome', 'objetivo', 'descricao']
    autocomplete_fields = ['responsavel', 'instancia_vinculada']
    filter_horizontal = ['pautas']
    inlines = [DocumentoGenericInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'descricao', 'objetivo', 'status'),
        }),
        ('Prazos', {
            'fields': ('data_inicio', 'data_fim_previsto', 'data_fim_real'),
        }),
        ('Recursos', {
            'fields': ('fonte_recurso', 'valor_orcado'),
        }),
        ('Vínculos', {
            'fields': ('responsavel', 'instancia_vinculada', 'pautas'),
        }),
    )
