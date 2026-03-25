"""Configuração do admin para Evento e Participação."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Evento, Participacao


class ParticipacaoInline(TabularInline):
    """Inline tabular de participações exibido no admin de Evento."""
    model = Participacao
    extra = 0
    fields = ['pessoa', 'municipio', 'forma_participacao', 'papel_no_evento', 'confirmado', 'pontos_calculados']
    readonly_fields = ['pontos_calculados']


@admin.register(Evento)
class EventoAdmin(ModelAdmin):
    """Admin de Evento com fieldsets de dados gerais e configuração de pontuação."""
    list_display = ['titulo', 'tipo', 'modalidade', 'data_inicio', 'data_fim', 'pontos_presencial', 'pontos_online']
    list_filter = ['tipo', 'modalidade', 'data_inicio']
    search_fields = ['titulo', 'descricao']
    inlines = [ParticipacaoInline]
    fieldsets = (
        ('Evento', {
            'fields': ('titulo', 'tipo', 'modalidade', 'data_inicio', 'data_fim', 'local', 'descricao'),
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
