"""Popula o banco com dados de demonstracao usando municipios reais."""

import random
import urllib.request
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.cadastro.models import Municipio, Pessoa, VinculoMunicipio
from aplicacoes.engajamento.models import ConfiguracaoEngajamento, Engajamento
from aplicacoes.eventos.models import Evento, Participacao


# Municipios reais — capitais e grandes cidades brasileiras
# (nome, uf, regiao, ibge, pop, associado, capital, lat, lng, brasao_wiki)
MUNICIPIOS = [
    # (nome, uf, regiao, ibge, pop, associado, capital, lat, lng, brasao_wiki)
    ('Sao Paulo', 'SP', 'sudeste', 3550308, 11_451_245, True, True,
     -23.5505, -46.6333, 'Bras%C3%A3o_da_cidade_de_S%C3%A3o_Paulo.svg'),
    ('Rio de Janeiro', 'RJ', 'sudeste', 3304557, 6_211_423, True, True,
     -22.9068, -43.1729, 'Bras%C3%A3o_da_cidade_do_Rio_de_Janeiro.svg'),
    ('Belo Horizonte', 'MG', 'sudeste', 3106200, 2_315_560, True, True,
     -19.9191, -43.9387, 'Bras%C3%A3o_de_Belo_Horizonte.svg'),
    ('Salvador', 'BA', 'nordeste', 2927408, 2_418_005, True, True,
     -12.9714, -38.5124, 'Bras%C3%A3o_de_Salvador.svg'),
    ('Curitiba', 'PR', 'sul', 4106902, 1_773_733, True, True,
     -25.4284, -49.2733, 'Bras%C3%A3o_de_Curitiba.svg'),
    ('Recife', 'PE', 'nordeste', 2611606, 1_488_920, True, True,
     -8.0476, -34.8770, 'Coat_of_arms_of_Recife.svg'),
    ('Porto Alegre', 'RS', 'sul', 4314902, 1_332_570, True, True,
     -30.0346, -51.2177, 'Bras%C3%A3o_de_Porto_Alegre.svg'),
    ('Goiania', 'GO', 'centro_oeste', 5208707, 1_437_237, True, True,
     -16.6799, -49.2550, 'Bras%C3%A3o_de_Goi%C3%A2nia.svg'),
    ('Fortaleza', 'CE', 'nordeste', 2304400, 2_428_678, True, True,
     -3.7172, -38.5433, 'Bras%C3%A3o_de_Fortaleza.svg'),
    ('Belem', 'PA', 'norte', 1501402, 1_303_403, False, True,
     -1.4558, -48.5024, 'Bras%C3%A3o_de_Bel%C3%A9m.svg'),
    ('Manaus', 'AM', 'norte', 1302603, 2_063_547, False, True,
     -3.1190, -60.0217, 'Bras%C3%A3o_de_Manaus.svg'),
    ('Florianopolis', 'SC', 'sul', 4205407, 508_826, True, True,
     -27.5954, -48.5480, 'Bras%C3%A3o_de_Florian%C3%B3polis.png'),
    ('Natal', 'RN', 'nordeste', 2408102, 751_300, True, True,
     -5.7945, -35.2110, 'Bras%C3%A3o_de_Natal.svg'),
    ('Campo Grande', 'MS', 'centro_oeste', 5002704, 786_797, True, True,
     -20.4697, -54.6201, 'Bras%C3%A3o_de_Campo_Grande.svg'),
    ('Campinas', 'SP', 'sudeste', 3509502, 1_139_047, True, False,
     -22.9099, -47.0626, 'Bras%C3%A3o_de_Campinas.png'),
]

# Nomes ficticios com seed para foto (pravatar.cc)
PESSOAS = [
    ('Carlos Mendonca', 'masculino', 'prefeito', 'PSD', 11),
    ('Ana Beatriz Rocha', 'feminino', 'prefeito', 'PT', 32),
    ('Roberto Ferreira', 'masculino', 'prefeito', 'MDB', 53),
    ('Fernanda Santos', 'feminino', 'prefeito', 'PSDB', 44),
    ('Jose Antonio Barbosa', 'masculino', 'prefeito', 'PP', 55),
    ('Mariana Costa', 'feminino', 'prefeito', 'PL', 26),
    ('Thiago Nascimento', 'masculino', 'prefeito', 'UNIAO', 67),
    ('Patricia Almeida', 'feminino', 'prefeito', 'PDT', 28),
    ('Marcos Vinicius Souza', 'masculino', 'prefeito', 'REPUBLICANOS', 59),
    ('Luciana Batista', 'feminino', 'prefeito', 'PSD', 40),
    ('Eduardo Carvalho', 'masculino', 'prefeito', 'MDB', 61),
    ('Juliana Pinheiro', 'feminino', 'prefeito', 'PT', 42),
    ('Rafael Moreira', 'masculino', 'prefeito', 'PP', 13),
    ('Camila Duarte', 'feminino', 'prefeito', 'PSDB', 34),
    ('Andre Goncalves', 'masculino', 'prefeito', 'PL', 15),
    ('Beatriz Farias', 'feminino', 'secretario', 'PSD', 46),
    ('Pedro Henrique Lima', 'masculino', 'secretario', 'PT', 57),
    ('Sofia Ribeiro', 'feminino', 'secretario', 'MDB', 38),
    ('Gustavo Teixeira', 'masculino', 'assessor', 'PSDB', 69),
    ('Isabela Monteiro', 'feminino', 'assessor', 'PP', 20),
    ('Daniel Correia', 'masculino', 'interno', '', 51),
    ('Larissa Campos', 'feminino', 'interno', '', 22),
    ('Felipe Araujo', 'masculino', 'interno', '', 63),
]

EVENTOS = [
    ('XXIII Reuniao Geral da FNP', 'reuniao_geral', 'presencial', '2025-03-15', '2025-03-17', 'Brasilia/DF'),
    ('Forum Nacional de Mobilidade Urbana', 'forum', 'hibrido', '2025-05-10', '2025-05-11', 'Sao Paulo/SP'),
    ('Webinar: Financas Municipais em 2025', 'webinar', 'online', '2025-04-22', None, 'Online'),
    ('Congresso de Prefeitos do Nordeste', 'congresso', 'presencial', '2025-06-08', '2025-06-10', 'Recife/PE'),
    ('Reuniao Online — Pauta Saude', 'reuniao_online', 'online', '2025-07-14', None, 'Online'),
    ('Viagem COP31 — Belem', 'viagem_internacional', 'presencial', '2025-11-10', '2025-11-21', 'Belem/PA'),
    ('Forum de Seguranca Publica', 'forum', 'presencial', '2025-08-20', '2025-08-21', 'Rio de Janeiro/RJ'),
    ('XXIV Reuniao Geral da FNP', 'reuniao_geral', 'presencial', '2026-03-12', '2026-03-14', 'Brasilia/DF'),
    ('Webinar: Transicao Energetica Municipal', 'webinar', 'online', '2026-02-18', None, 'Online'),
    ('Reuniao Presencial — Infraestrutura', 'reuniao_presencial', 'presencial', '2026-01-25', None, 'Brasilia/DF'),
]


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstracao (municipios reais)'

    def _baixar_brasoes(self):
        """Baixa brasoes reais do Wikimedia Commons."""
        destino = Path(settings.BASE_DIR) / 'estaticos' / 'img' / 'brasoes'
        destino.mkdir(parents=True, exist_ok=True)
        base_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/'

        for nome, _, _, ibge, *_, brasao_wiki in MUNICIPIOS:
            ext = 'svg' if brasao_wiki.endswith('.svg') else 'png'
            arquivo = destino / f'{ibge}.{ext}'
            if arquivo.exists():
                continue
            url = f'{base_url}{brasao_wiki}?width=200'
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'SistemaFNP/1.0 (contato@fnp.org.br) Python/3'
                })
                with urllib.request.urlopen(req) as resp:
                    arquivo.write_bytes(resp.read())
                self.stdout.write(f'    Brasao baixado: {nome}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'    Falha ao baixar brasao de {nome}: {e}'))

    def handle(self, *args, **options):
        self.stdout.write('Limpando dados antigos de mockup...')
        Participacao.objects.all().delete()
        Engajamento.objects.all().delete()
        Adimplencia.objects.all().delete()
        Evento.objects.all().delete()
        VinculoMunicipio.objects.all().delete()
        Pessoa.objects.all().delete()
        Municipio.objects.all().delete()
        ConfiguracaoEngajamento.objects.all().delete()

        self.stdout.write('\nBaixando brasoes reais...')
        self._baixar_brasoes()

        self.stdout.write('\nCriando dados de demonstracao...')

        # Municipios
        municipios = []
        for nome, uf, regiao, ibge, pop, associado, capital, lat, lng, _ in MUNICIPIOS:
            m = Municipio.objects.create(
                nome=nome, uf=uf, regiao=regiao, codigo_ibge=ibge,
                populacao=pop, associado_fnp=associado, eh_capital=capital,
                latitude=lat, longitude=lng,
            )
            municipios.append(m)
        self.stdout.write(f'  {len(municipios)} municipios criados')

        # Pessoas
        pessoas = []
        for nome, genero, tipo, partido, seed in PESSOAS:
            email = f'{nome.lower().split()[0]}.{nome.lower().split()[-1]}@exemplo.gov.br'
            p = Pessoa.objects.create(
                nome=nome, email=email, tipo=tipo, genero=genero,
                partido=partido, ativo=True,
                mandato_inicio=date(2025, 1, 1) if tipo in ('prefeito', 'vice_prefeito') else None,
                mandato_fim=date(2028, 12, 31) if tipo in ('prefeito', 'vice_prefeito') else None,
            )
            pessoas.append(p)
        self.stdout.write(f'  {len(pessoas)} pessoas criadas')

        # Vinculos
        prefeitos = [p for p in pessoas if p.tipo == 'prefeito']
        for i, prefeito in enumerate(prefeitos):
            if i < len(municipios):
                VinculoMunicipio.objects.create(
                    pessoa=prefeito, municipio=municipios[i],
                    papel='prefeito', inicio_mandato=date(2025, 1, 1),
                    fim_mandato=date(2028, 12, 31), vigente=True,
                )
        outros = [p for p in pessoas if p.tipo in ('secretario', 'assessor')]
        for pessoa in outros:
            mun = random.choice(municipios[:10])
            VinculoMunicipio.objects.create(
                pessoa=pessoa, municipio=mun, papel=pessoa.tipo,
                inicio_mandato=date(2025, 1, 1), vigente=True,
            )
        self.stdout.write('  Vinculos criados')

        # Adimplencia
        for mun in municipios:
            for ano in [2025, 2026]:
                if mun.associado_fnp:
                    status = random.choices(['adimplente', 'inadimplente', 'parcial'], weights=[60, 20, 20])[0]
                    valor_devido = Decimal(random.randint(15000, 80000))
                    valor_pago = valor_devido if status == 'adimplente' else (valor_devido * Decimal('0.5') if status == 'parcial' else Decimal(0))
                else:
                    status = 'inadimplente'
                    valor_devido = Decimal(random.randint(10000, 30000))
                    valor_pago = Decimal(0)
                Adimplencia.objects.create(
                    municipio=mun, ano_referencia=ano, status=status,
                    valor_devido=valor_devido, valor_pago=valor_pago,
                    data_pagamento=date(ano, random.randint(1, 6), 15) if valor_pago > 0 else None,
                )
        self.stdout.write('  Adimplencia criada')

        # Eventos
        eventos = []
        for titulo, tipo, modalidade, inicio, fim, local in EVENTOS:
            ev = Evento.objects.create(
                titulo=titulo, tipo=tipo, modalidade=modalidade,
                data_inicio=date.fromisoformat(inicio),
                data_fim=date.fromisoformat(fim) if fim else None,
                local=local,
            )
            eventos.append(ev)
        self.stdout.write(f'  {len(eventos)} eventos criados')

        # Participacoes
        total = 0
        for evento in eventos:
            n = random.randint(5, min(13, len(prefeitos)))
            for prefeito in random.sample(prefeitos, n):
                vinculo = prefeito.vinculos.filter(vigente=True).first()
                if not vinculo:
                    continue
                forma = 'presencial' if evento.modalidade in ('presencial', 'hibrido') else 'online'
                if evento.modalidade == 'hibrido':
                    forma = random.choice(['presencial', 'online'])
                papel = random.choices(['participante', 'palestrante', 'organizador', 'moderador'], weights=[70, 15, 10, 5])[0]
                Participacao.objects.create(
                    pessoa=prefeito, evento=evento, municipio=vinculo.municipio,
                    forma_participacao=forma, papel_no_evento=papel,
                    confirmado=True, data_confirmacao=timezone.now(),
                )
                total += 1
        self.stdout.write(f'  {total} participacoes criadas')

        # Engajamento — recalcular (signals ja criaram alguns)
        config = ConfiguracaoEngajamento.atual()
        for mun in municipios:
            eng, _ = Engajamento.objects.get_or_create(
                municipio=mun, bienio=config.bienio_atual,
            )
            eng.recalcular()
        self.stdout.write('  Engajamento recalculado')

        self.stdout.write(self.style.SUCCESS('\nMockup com dados reais criado com sucesso!'))
