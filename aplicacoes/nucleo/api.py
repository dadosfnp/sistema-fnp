"""API REST publica para integracao externa (PowerBI, prefeituras, BI).

Apenas leitura por enquanto — endpoints retornam dados ja sanitizados (sem
campos sensiveis tipo telefone/email/CPF). Throttle ativo em REST_FRAMEWORK
para evitar scraping abusivo.

Autenticacao:
- Token via ``Authorization: Token <chave>`` (cliente externo)
- Sessao Django (browser logado)

Para gerar token para um usuario:
    python manage.py drf_create_token <username>
"""

from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.engajamento.models import Engajamento


class MunicipioSerializer(serializers.ModelSerializer):
    regiao_label = serializers.CharField(source='get_regiao_display', read_only=True)
    adimplencia_atual = serializers.CharField(read_only=True)

    class Meta:
        model = Municipio
        fields = (
            'id', 'nome', 'uf', 'codigo_ibge', 'regiao', 'regiao_label',
            'populacao', 'eh_capital', 'associado_fnp', 'adimplencia_atual',
        )


class PessoaPublicaSerializer(serializers.ModelSerializer):
    """Versao publica de Pessoa — OMITE telefone, email, foto e observacoes (LGPD)."""

    tipo_label = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Pessoa
        fields = ('id', 'nome', 'tipo', 'tipo_label', 'cargo', 'partido', 'ativo')


class EngajamentoSerializer(serializers.ModelSerializer):
    municipio_nome = serializers.CharField(source='municipio.nome', read_only=True)
    municipio_uf = serializers.CharField(source='municipio.uf', read_only=True)
    nivel_label = serializers.CharField(source='get_nivel_display', read_only=True)

    class Meta:
        model = Engajamento
        fields = (
            'id', 'municipio', 'municipio_nome', 'municipio_uf',
            'bienio', 'pontuacao_bruta', 'pontuacao_normalizada',
            'nivel', 'nivel_label', 'total_participacoes', 'ultima_atualizacao',
        )


class MunicipioViewSet(viewsets.ReadOnlyModelViewSet):
    """Listagem e detalhe de municipios. Filtros via query string."""

    queryset = Municipio.objects.all().order_by('nome')
    serializer_class = MunicipioSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get('uf'):
            qs = qs.filter(uf=params['uf'].upper())
        if params.get('regiao'):
            qs = qs.filter(regiao=params['regiao'])
        if params.get('associado') == 'true':
            qs = qs.filter(associado_fnp=True)
        if params.get('busca'):
            qs = qs.filter(nome__icontains=params['busca'])
        return qs

    @action(detail=True, methods=['get'])
    def indice_fnp(self, request, pk=None):
        """Retorna o Indice FNP composto do municipio."""
        from aplicacoes.engajamento.servicos.indice_fnp import calcular_indice
        municipio = self.get_object()
        return Response(calcular_indice(municipio))


class PessoaViewSet(viewsets.ReadOnlyModelViewSet):
    """Listagem publica de pessoas — sem dados sensiveis."""

    queryset = Pessoa.objects.filter(ativo=True).order_by('nome')
    serializer_class = PessoaPublicaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get('tipo'):
            qs = qs.filter(tipo=params['tipo'])
        if params.get('busca'):
            qs = qs.filter(nome__icontains=params['busca'])
        return qs


class EngajamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """Engajamentos por municipio/bienio."""

    queryset = Engajamento.objects.select_related('municipio').order_by('-pontuacao_bruta')
    serializer_class = EngajamentoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get('uf'):
            qs = qs.filter(municipio__uf=params['uf'].upper())
        if params.get('nivel'):
            qs = qs.filter(nivel=params['nivel'])
        if params.get('bienio'):
            qs = qs.filter(bienio=params['bienio'])
        return qs
