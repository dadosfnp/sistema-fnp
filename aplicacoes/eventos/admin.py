"""Configuração do admin para Evento e Participação."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from aplicacoes.documentos.admin import DocumentoGenericInline

from .models import Evento, Participacao


class ParticipacaoInline(TabularInline):
    """Inline tabular de participações exibido no admin de Evento."""
    model = Participacao
    extra = 0
    fields = ['pessoa', 'municipio', 'forma_participacao', 'papel_no_evento', 'confirmado', 'pontos_calculados']
    readonly_fields = ['pontos_calculados']
    autocomplete_fields = ['pessoa', 'municipio']


@admin.register(Evento)
class EventoAdmin(ModelAdmin):
    """Admin de Evento com fieldsets de dados gerais, classificação e pontuação."""
    list_display = [
        'titulo',
        'tipo',
        'acesso',
        'natureza',
        'modalidade',
        'data_inicio',
        'data_fim',
        'pontos_presencial',
        'pontos_online',
    ]
    list_filter = ['tipo', 'acesso', 'objetivo', 'natureza', 'modalidade', 'data_inicio']
    search_fields = ['titulo', 'descricao', 'cidade']
    autocomplete_fields = ['instancia_vinculada']
    inlines = [ParticipacaoInline, DocumentoGenericInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('titulo', 'tipo', 'descricao'),
        }),
        ('Classificação', {
            'fields': ('acesso', 'objetivo', 'natureza', 'tipo_participacao_fnp', 'modalidade'),
        }),
        ('Datas e local', {
            'fields': ('data_inicio', 'data_fim', 'local', 'cidade', 'uf'),
        }),
        ('Vínculos', {
            'fields': ('instancia_vinculada',),
        }),
        ('Pontuação', {
            'fields': ('pontos_presencial', 'pontos_online', 'pontos_palestrante_bonus', 'pontos_organizador_bonus'),
        }),
    )


@admin.register(Participacao)
class ParticipacaoAdmin(ModelAdmin):
    """Admin de Participação com pontos calculados somente-leitura e autocomplete."""
    list_display = ['pessoa', 'evento', 'municipio', 'forma_participacao', 'papel_no_evento', 'confirmado', 'pontos_calculados']
    list_filter = ['forma_participacao', 'papel_no_evento', 'confirmado']
    search_fields = ['pessoa__nome', 'evento__titulo', 'municipio__nome']
    autocomplete_fields = ['pessoa', 'evento', 'municipio']
    readonly_fields = ['pontos_calculados']
