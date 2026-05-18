"""Admin Unfold para termos do dicionário institucional."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import TermoDicionario


@admin.register(TermoDicionario)
class TermoDicionarioAdmin(ModelAdmin):
    """Admin de TermoDicionario com filtros por seção e ordenação."""
    list_display = ['termo', 'secao', 'ordem', 'ativo']
    list_filter = ['secao', 'ativo']
    search_fields = ['termo', 'definicao', 'tipo_de_dado']
    list_editable = ['ordem', 'ativo']
    fieldsets = (
        ('Identificação', {
            'fields': ('termo', 'secao', 'ordem', 'ativo'),
        }),
        ('Conteúdo', {
            'fields': ('definicao', 'tipo_de_dado'),
        }),
    )
