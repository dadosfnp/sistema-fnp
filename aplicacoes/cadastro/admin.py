"""Configuração do admin para Pessoa, Município, Pauta e VínculoMunicípio."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import EnvolvimentoPauta, Municipio, Pauta, Pessoa, VinculoMunicipio


class VinculoInline(TabularInline):
    """Inline tabular de vínculos municipais exibido no admin de Pessoa."""
    model = VinculoMunicipio
    extra = 0
    fields = ['municipio', 'papel', 'inicio_mandato', 'fim_mandato', 'vigente']


class EnvolvimentoPautaInline(TabularInline):
    """Inline tabular de envolvimentos em pautas exibido no admin de Pessoa."""
    model = EnvolvimentoPauta
    extra = 0
    fields = ['pauta', 'nivel', 'observacao']


@admin.register(Pessoa)
class PessoaAdmin(ModelAdmin):
    """Admin de Pessoa com fieldsets organizados e inlines de vínculo e pauta."""
    list_display = ['nome', 'tipo', 'cargo', 'partido', 'genero', 'autorizacao_uso_imagem', 'ativo']
    list_filter = ['tipo', 'ativo', 'genero', 'partido', 'autorizacao_uso_imagem', 'termo_confidencialidade']
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
        ('Documentos e termos', {
            'fields': ('autorizacao_uso_imagem', 'termo_confidencialidade'),
        }),
        ('Perfil', {
            'fields': ('redes_sociais', 'biografia_curta', 'observacoes'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Municipio)
class MunicipioAdmin(ModelAdmin):
    """Admin de Município com fieldsets de identificação, dados e localização."""
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
    """Admin de Pauta temática com filtro por status ativa/inativa."""
    list_display = ['nome', 'ativa']
    list_filter = ['ativa']
    search_fields = ['nome']


@admin.register(VinculoMunicipio)
class VinculoMunicipioAdmin(ModelAdmin):
    """Admin de VínculoMunicípio com autocomplete de pessoa e município."""
    list_display = ['pessoa', 'municipio', 'papel', 'inicio_mandato', 'fim_mandato', 'vigente']
    list_filter = ['papel', 'vigente']
    search_fields = ['pessoa__nome', 'municipio__nome']
    autocomplete_fields = ['pessoa', 'municipio']
