from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Adimplencia


@admin.register(Adimplencia)
class AdimplenciaAdmin(ModelAdmin):
    list_display = [
        'municipio', 'ano_referencia', 'status',
        'valor_devido', 'valor_pago', 'data_pagamento',
    ]
    list_filter = ['status', 'ano_referencia']
    search_fields = ['municipio__nome']
    autocomplete_fields = ['municipio']
