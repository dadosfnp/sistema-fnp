"""Configuração do admin para o model Adimplência."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Adimplencia


@admin.register(Adimplencia)
class AdimplenciaAdmin(ModelAdmin):
    """Admin de Adimplência com filtros por status e ano de referência."""
    list_display = [
        'municipio', 'ano_referencia', 'status',
        'valor_devido', 'valor_pago', 'data_pagamento',
    ]
    list_filter = ['status', 'ano_referencia']
    search_fields = ['municipio__nome']
    autocomplete_fields = ['municipio']
