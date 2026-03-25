from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import EnvolvimentoPauta, Municipio, Pauta, Pessoa, VinculoMunicipio


class VinculoInline(TabularInline):
    model = VinculoMunicipio
    extra = 0
    fields = ['municipio', 'papel', 'inicio_mandato', 'fim_mandato', 'vigente']


class EnvolvimentoPautaInline(TabularInline):
    model = EnvolvimentoPauta
    extra = 0
    fields = ['pauta', 'nivel', 'observacao']


@admin.register(Pessoa)
class PessoaAdmin(ModelAdmin):
    list_display = ['nome', 'tipo', 'cargo', 'partido', 'genero', 'ativo']
    list_filter = ['tipo', 'ativo', 'genero', 'partido']
    search_fields = ['nome', 'email', 'cargo']
    list_editable = ['ativo']
    inlines = [VinculoInline, EnvolvimentoPautaInline]
    fieldsets = (
        ('Dados pessoais', {
            'fields': ('nome', 'foto', 'email', 'telefone', 'genero'),
        }),
        ('Dados institucionais', {
            'fields': ('tipo', 'cargo', 'partido', 'mandato_inicio', 'mandato_fim', 'ativo'),
        }),
        ('Perfil', {
            'fields': ('redes_sociais', 'biografia_curta', 'observacoes'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Municipio)
class MunicipioAdmin(ModelAdmin):
    list_display = ['nome', 'uf', 'regiao', 'populacao', 'eh_capital', 'associado_fnp']
    list_filter = ['uf', 'regiao', 'eh_capital', 'associado_fnp']
    search_fields = ['nome', 'codigo_ibge']
    list_editable = ['associado_fnp']
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'uf', 'codigo_ibge', 'regiao'),
        }),
        ('Dados', {
            'fields': ('populacao', 'eh_capital', 'associado_fnp'),
        }),
        ('Localização (mapa)', {
            'fields': ('latitude', 'longitude'),
        }),
    )


@admin.register(Pauta)
class PautaAdmin(ModelAdmin):
    list_display = ['nome', 'ativa']
    list_filter = ['ativa']
    search_fields = ['nome']


@admin.register(VinculoMunicipio)
class VinculoMunicipioAdmin(ModelAdmin):
    list_display = ['pessoa', 'municipio', 'papel', 'inicio_mandato', 'fim_mandato', 'vigente']
    list_filter = ['papel', 'vigente']
    search_fields = ['pessoa__nome', 'municipio__nome']
    autocomplete_fields = ['pessoa', 'municipio']
