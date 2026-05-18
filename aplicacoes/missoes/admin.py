"""Admin Unfold para Missões e Membros da Delegação."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from aplicacoes.documentos.admin import DocumentoGenericInline

from .models import MembroDelegacao, Missao


class MembroDelegacaoInline(TabularInline):
    """Inline de membros da delegação dentro do admin de Missão."""
    model = MembroDelegacao
    extra = 0
    fields = ['pessoa', 'papel', 'observacao']
    autocomplete_fields = ['pessoa']


@admin.register(Missao)
class MissaoAdmin(ModelAdmin):
    """Admin de Missão com inline de delegação e fieldsets organizados."""
    list_display = ['titulo', 'tipo', 'status', 'pais', 'cidade', 'data_inicio', 'data_fim']
    list_filter = ['tipo', 'status']
    search_fields = ['titulo', 'objetivo', 'pais', 'cidade']
    autocomplete_fields = ['chefe_delegacao', 'instancia_vinculada']
    inlines = [MembroDelegacaoInline, DocumentoGenericInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('titulo', 'tipo', 'status', 'objetivo'),
        }),
        ('Destino', {
            'fields': ('pais', 'cidade'),
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_fim'),
        }),
        ('Delegação e vínculos', {
            'fields': ('chefe_delegacao', 'instancia_vinculada'),
        }),
        ('Resultado', {
            'fields': ('relatorio_resumo',),
        }),
    )


@admin.register(MembroDelegacao)
class MembroDelegacaoAdmin(ModelAdmin):
    """Admin direto de membros da delegação, útil para buscas cross-missão."""
    list_display = ['pessoa', 'missao', 'papel']
    list_filter = ['papel']
    search_fields = ['pessoa__nome', 'missao__titulo']
    autocomplete_fields = ['pessoa', 'missao']
