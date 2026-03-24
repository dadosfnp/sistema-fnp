from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Evento, Participacao


class ParticipacaoInline(admin.TabularInline):
    model = Participacao
    extra = 0
    fields = ['pessoa', 'tipo_participacao', 'confirmado', 'data_confirmacao']


@admin.register(Evento)
class EventoAdmin(ModelAdmin):
    list_display = ['titulo', 'tipo', 'data_inicio', 'data_fim', 'local', 'peso_engajamento']
    list_filter = ['tipo', 'data_inicio']
    search_fields = ['titulo', 'descricao']
    inlines = [ParticipacaoInline]


@admin.register(Participacao)
class ParticipacaoAdmin(ModelAdmin):
    list_display = ['pessoa', 'evento', 'tipo_participacao', 'confirmado', 'data_confirmacao']
    list_filter = ['tipo_participacao', 'confirmado']
    search_fields = ['pessoa__nome', 'evento__titulo']
    autocomplete_fields = ['pessoa', 'evento']
