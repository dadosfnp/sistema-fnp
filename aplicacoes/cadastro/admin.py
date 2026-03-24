from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Municipio, Pessoa, VinculoMunicipio


class VinculoInline(admin.TabularInline):
    model = VinculoMunicipio
    extra = 0
    fields = ['municipio', 'papel', 'inicio_mandato', 'fim_mandato', 'vigente']


@admin.register(Pessoa)
class PessoaAdmin(ModelAdmin):
    list_display = ['nome', 'tipo', 'email', 'cargo', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'email', 'cargo']
    list_editable = ['ativo']
    inlines = [VinculoInline]


@admin.register(Municipio)
class MunicipioAdmin(ModelAdmin):
    list_display = ['nome', 'uf', 'codigo_ibge', 'populacao', 'eh_capital', 'associado_fnp']
    list_filter = ['uf', 'eh_capital', 'associado_fnp', 'regiao']
    search_fields = ['nome', 'codigo_ibge']
    list_editable = ['associado_fnp']


@admin.register(VinculoMunicipio)
class VinculoMunicipioAdmin(ModelAdmin):
    list_display = ['pessoa', 'municipio', 'papel', 'inicio_mandato', 'fim_mandato', 'vigente']
    list_filter = ['papel', 'vigente']
    search_fields = ['pessoa__nome', 'municipio__nome']
    autocomplete_fields = ['pessoa', 'municipio']
