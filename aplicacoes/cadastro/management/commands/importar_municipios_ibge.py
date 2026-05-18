"""Importa os 5.570+ municípios brasileiros direto da API pública do IBGE.

A API ``servicodados.ibge.gov.br/api/v1/localidades/municipios`` é estável,
gratuita e não exige autenticação. Esta importação usa ``bulk_create`` em
lotes para suportar a escala completa em poucos segundos.

Uso:
    python manage.py importar_municipios_ibge          # busca tudo (lento na 1ª vez)
    python manage.py importar_municipios_ibge --uf SP  # só uma UF
    python manage.py importar_municipios_ibge --limpar # remove existentes antes
"""

import time
import urllib.request
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from aplicacoes.cadastro.models import Municipio


URL_API = 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios'
# Marcador de cache no disco — guarda ETag e Last-Modified da última resposta
# para evitar baixar 5.570 registros desnecessariamente.
CACHE_DIR = Path(settings.BASE_DIR) / '.cache' / 'ibge'
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_META = CACHE_DIR / 'meta.json'

# Mapa UF -> região
REGIAO_POR_UF = {
    'AC': 'norte', 'AP': 'norte', 'AM': 'norte', 'PA': 'norte',
    'RO': 'norte', 'RR': 'norte', 'TO': 'norte',
    'AL': 'nordeste', 'BA': 'nordeste', 'CE': 'nordeste', 'MA': 'nordeste',
    'PB': 'nordeste', 'PE': 'nordeste', 'PI': 'nordeste', 'RN': 'nordeste',
    'SE': 'nordeste',
    'DF': 'centro_oeste', 'GO': 'centro_oeste', 'MT': 'centro_oeste', 'MS': 'centro_oeste',
    'ES': 'sudeste', 'MG': 'sudeste', 'RJ': 'sudeste', 'SP': 'sudeste',
    'PR': 'sul', 'RS': 'sul', 'SC': 'sul',
}

# Capitais brasileiras (códigos IBGE)
CAPITAIS_IBGE = {
    1200401, 2704302, 1302603, 1400100, 2927408, 2304400, 5300108, 3205309,
    5208707, 2111300, 5103403, 5002704, 3106200, 1501402, 2507507, 4106902,
    2611606, 2211001, 3304557, 2408102, 4314902, 1100205, 1400100, 4205407,
    3550308, 2800308, 1721000,
}


def _ler_meta_cache():
    """Carrega ETag e Last-Modified da resposta anterior (se houver)."""
    if not CACHE_META.exists():
        return {}
    try:
        return json.loads(CACHE_META.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _gravar_meta_cache(meta):
    CACHE_META.write_text(json.dumps(meta), encoding='utf-8')


def _buscar_da_api(url, tentativas=3, delay=2, usar_cache=True):
    """Requisição com retry, timeout e suporte a ETag/Last-Modified.

    Returns:
        Tupla (dados, nao_modificado). ``dados`` é lista de dicts ou None.
        ``nao_modificado`` é True se o servidor respondeu 304 (sem alteração).
    """
    meta = _ler_meta_cache() if usar_cache else {}
    req = urllib.request.Request(url)
    if meta.get('etag'):
        req.add_header('If-None-Match', meta['etag'])
    if meta.get('last_modified'):
        req.add_header('If-Modified-Since', meta['last_modified'])

    for tentativa in range(tentativas):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                novo_meta = {
                    'etag': resp.headers.get('ETag', ''),
                    'last_modified': resp.headers.get('Last-Modified', ''),
                }
                _gravar_meta_cache(novo_meta)
                return json.loads(resp.read().decode('utf-8')), False
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                return None, True
            if tentativa == tentativas - 1:
                raise
            time.sleep(delay)
        except Exception:
            if tentativa == tentativas - 1:
                raise
            time.sleep(delay)
    return None, False


class Command(BaseCommand):
    """Importa municípios brasileiros da API do IBGE."""

    help = 'Importa os 5.570+ municípios brasileiros da API do IBGE.'

    def add_arguments(self, parser):
        parser.add_argument('--uf', help='Importar apenas uma UF (ex.: SP)')
        parser.add_argument(
            '--limpar', action='store_true',
            help='Apaga todos os municípios não-associados antes de importar.',
        )
        parser.add_argument(
            '--lote', type=int, default=500,
            help='Tamanho do lote de bulk_create (padrão 500).',
        )
        parser.add_argument(
            '--forcar', action='store_true',
            help='Ignora cache de ETag e força refetch completo.',
        )

    def handle(self, *args, **options):
        uf_filtro = (options.get('uf') or '').upper()

        if options['limpar']:
            removidos = Municipio.objects.filter(associado_fnp=False).delete()
            self.stdout.write(self.style.WARNING(
                f'Removidos {removidos[0]} municípios não-associados antes da importação.'
            ))

        self.stdout.write('Buscando municípios na API do IBGE...')
        dados, nao_modificado = _buscar_da_api(URL_API, usar_cache=not options['forcar'])
        if nao_modificado:
            self.stdout.write(self.style.SUCCESS(
                'IBGE respondeu 304 — base já está atualizada. Use --forcar para reimportar.'
            ))
            return
        if not dados:
            self.stdout.write(self.style.ERROR('Falha ao buscar dados do IBGE.'))
            return

        if uf_filtro:
            dados = [d for d in dados if d.get('microrregiao', {}).get('mesorregiao', {}).get('UF', {}).get('sigla') == uf_filtro]

        self.stdout.write(f'Total de municípios da API: {len(dados)}')

        existentes = set(Municipio.objects.values_list('codigo_ibge', flat=True))
        novos = []
        para_atualizar = []

        for d in dados:
            codigo_ibge = d['id']
            nome = d['nome']
            uf = d.get('microrregiao', {}).get('mesorregiao', {}).get('UF', {}).get('sigla', '')
            regiao = REGIAO_POR_UF.get(uf, '')
            eh_capital = codigo_ibge in CAPITAIS_IBGE

            if codigo_ibge in existentes:
                # Atualiza só campos básicos para preservar associado_fnp, brasão, etc.
                para_atualizar.append((codigo_ibge, nome, uf, regiao, eh_capital))
            else:
                novos.append(Municipio(
                    codigo_ibge=codigo_ibge, nome=nome, uf=uf,
                    regiao=regiao, eh_capital=eh_capital,
                    populacao=0, associado_fnp=False,
                ))

        lote = options['lote']

        with transaction.atomic():
            for i in range(0, len(novos), lote):
                Municipio.objects.bulk_create(novos[i:i + lote])
                self.stdout.write(f'  Inseridos {min(i + lote, len(novos))}/{len(novos)}...')

            for codigo_ibge, nome, uf, regiao, eh_capital in para_atualizar:
                Municipio.objects.filter(codigo_ibge=codigo_ibge).update(
                    nome=nome, uf=uf, regiao=regiao, eh_capital=eh_capital,
                )

        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {len(novos)} criados, {len(para_atualizar)} atualizados.'
        ))
