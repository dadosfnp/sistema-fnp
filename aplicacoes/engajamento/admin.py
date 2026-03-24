from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Engajamento


@admin.register(Engajamento)
class EngajamentoAdmin(ModelAdmin):
    list_display = ['municipio', 'pontuacao_total', 'total_participacoes', 'nivel', 'ultima_interacao']
    list_filter = ['nivel']
    search_fields = ['municipio__nome']
    readonly_fields = ['pontuacao_total', 'total_participacoes', 'ultima_interacao', 'nivel']
    autocomplete_fields = ['municipio']
