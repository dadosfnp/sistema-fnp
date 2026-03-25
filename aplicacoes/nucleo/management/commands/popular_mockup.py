import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from aplicacoes.cadastro.models import Municipio, Pessoa, VinculoMunicipio
from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.engajamento.models import ConfiguracaoEngajamento, Engajamento
from aplicacoes.eventos.models import Evento, Participacao


MUNICIPIOS_FICTICIOS = [
    # (nome, uf, regiao, ibge, pop, associado, lat, lng)
    ('Porto Esperanca', 'RS', 'sul', 4314902, 1_500_000, True, -30.0346, -51.2177),
    ('Nova Alvorada', 'SP', 'sudeste', 3550308, 12_300_000, True, -23.5505, -46.6333),
    ('Serra Dourada', 'MG', 'sudeste', 3106200, 2_500_000, True, -19.9167, -43.9345),
    ('Recanto do Sol', 'BA', 'nordeste', 2927408, 2_900_000, True, -12.9714, -38.5124),
    ('Vila Progresso', 'PR', 'sul', 4106902, 1_900_000, True, -25.4284, -49.2733),
    ('Bela Vista do Norte', 'PA', 'norte', 1501402, 1_500_000, False, -1.4558, -48.5024),
    ('Campo Florido', 'GO', 'centro_oeste', 5208707, 1_600_000, True, -16.6799, -49.2550),
    ('Pedra Azul', 'RJ', 'sudeste', 3304557, 6_700_000, True, -22.9068, -43.1729),
    ('Lago Sereno', 'AM', 'norte', 1302603, 2_200_000, False, -3.1190, -60.0217),
    ('Monte Alegre do Sul', 'CE', 'nordeste', 2304400, 2_700_000, True, -3.7172, -38.5433),
    ('Rio Claro do Oeste', 'MT', 'centro_oeste', 5103403, 620_000, False, -15.5960, -56.0969),
    ('Estrela do Mar', 'SC', 'sul', 4205407, 600_000, True, -27.5954, -48.5480),
    ('Palmas Novas', 'TO', 'norte', 1721000, 310_000, False, -10.1689, -48.3317),
    ('Jardim das Flores', 'PE', 'nordeste', 2611606, 1_650_000, True, -8.0476, -34.8770),
    ('Cachoeira Alta', 'ES', 'sudeste', 3205309, 400_000, True, -20.3155, -40.3128),
]

NOMES_FICTICIOS = [
    ('Carlos Mendonça', 'masculino', 'prefeito', 'PSD'),
    ('Ana Beatriz Rocha', 'feminino', 'prefeito', 'PT'),
    ('Roberto Ferreira Lima', 'masculino', 'prefeito', 'MDB'),
    ('Fernanda Oliveira Santos', 'feminino', 'prefeito', 'PSDB'),
    ('José Antônio Barbosa', 'masculino', 'prefeito', 'PP'),
    ('Mariana Costa Silva', 'feminino', 'prefeito', 'PL'),
    ('Thiago Nascimento', 'masculino', 'prefeito', 'UNIÃO'),
    ('Patrícia Almeida', 'feminino', 'prefeito', 'PDT'),
    ('Marcos Vinícius Souza', 'masculino', 'prefeito', 'REPUBLICANOS'),
    ('Luciana Batista Reis', 'feminino', 'prefeito', 'PSD'),
    ('Eduardo Carvalho', 'masculino', 'prefeito', 'MDB'),
    ('Juliana Pinheiro', 'feminino', 'prefeito', 'PT'),
    ('Rafael Moreira', 'masculino', 'prefeito', 'PP'),
    ('Camila Duarte', 'feminino', 'prefeito', 'PSDB'),
    ('André Gonçalves', 'masculino', 'prefeito', 'PL'),
    ('Beatriz Farias', 'feminino', 'secretario', 'PSD'),
    ('Pedro Henrique Lima', 'masculino', 'secretario', 'PT'),
    ('Sofia Ribeiro', 'feminino', 'secretario', 'MDB'),
    ('Gustavo Teixeira', 'masculino', 'assessor', 'PSDB'),
    ('Isabela Monteiro', 'feminino', 'assessor', 'PP'),
    ('Daniel Correia', 'masculino', 'interno', ''),
    ('Larissa Campos', 'feminino', 'interno', ''),
    ('Felipe Araújo', 'masculino', 'interno', ''),
]

EVENTOS_FICTICIOS = [
    ('XXIII Reunião Geral da FNP', 'reuniao_geral', 'presencial', '2025-03-15', '2025-03-17', 'Brasília/DF'),
    ('Fórum Nacional de Mobilidade Urbana', 'forum', 'hibrido', '2025-05-10', '2025-05-11', 'São Paulo/SP'),
    ('Webinar: Finanças Municipais em 2025', 'webinar', 'online', '2025-04-22', None, 'Online'),
    ('Congresso de Prefeitos do Nordeste', 'congresso', 'presencial', '2025-06-08', '2025-06-10', 'Recife/PE'),
    ('Reunião Online — Pauta Saúde', 'reuniao_online', 'online', '2025-07-14', None, 'Online'),
    ('Viagem COP31 — Belém', 'viagem_internacional', 'presencial', '2025-11-10', '2025-11-21', 'Belém/PA'),
    ('Fórum de Segurança Pública', 'forum', 'presencial', '2025-08-20', '2025-08-21', 'Rio de Janeiro/RJ'),
    ('XXIV Reunião Geral da FNP', 'reuniao_geral', 'presencial', '2026-03-12', '2026-03-14', 'Brasília/DF'),
    ('Webinar: Transição Energética Municipal', 'webinar', 'online', '2026-02-18', None, 'Online'),
    ('Reunião Presencial — Infraestrutura', 'reuniao_presencial', 'presencial', '2026-01-25', None, 'Brasília/DF'),
]


class Command(BaseCommand):
    help = 'Popula o banco com dados fictícios para demonstração'

    def handle(self, *args, **options):
        self.stdout.write('Criando dados de mockup...\n')

        # Municípios
        municipios = []
        for nome, uf, regiao, ibge, pop, associado, lat, lng in MUNICIPIOS_FICTICIOS:
            m, created = Municipio.objects.get_or_create(
                codigo_ibge=ibge,
                defaults={
                    'nome': nome,
                    'uf': uf,
                    'regiao': regiao,
                    'populacao': pop,
                    'associado_fnp': associado,
                    'eh_capital': pop > 2_000_000,
                    'latitude': lat,
                    'longitude': lng,
                },
            )
            if not created and not m.latitude:
                m.latitude = lat
                m.longitude = lng
                m.save(update_fields=['latitude', 'longitude'])
            municipios.append(m)
        self.stdout.write(f'  {len(municipios)} municípios criados/existentes')

        # Pessoas
        pessoas = []
        for i, (nome, genero, tipo, partido) in enumerate(NOMES_FICTICIOS):
            email = f'{nome.lower().split()[0]}.{nome.lower().split()[-1]}@exemplo.gov.br'
            p, _ = Pessoa.objects.get_or_create(
                nome=nome,
                defaults={
                    'email': email,
                    'tipo': tipo,
                    'genero': genero,
                    'partido': partido,
                    'ativo': True,
                    'mandato_inicio': date(2025, 1, 1) if tipo in ('prefeito', 'vice_prefeito') else None,
                    'mandato_fim': date(2028, 12, 31) if tipo in ('prefeito', 'vice_prefeito') else None,
                },
            )
            pessoas.append(p)
        self.stdout.write(f'  {len(pessoas)} pessoas criadas/existentes')

        # Vínculos (prefeitos → municípios)
        prefeitos = [p for p in pessoas if p.tipo == 'prefeito']
        for i, prefeito in enumerate(prefeitos):
            if i < len(municipios):
                VinculoMunicipio.objects.get_or_create(
                    pessoa=prefeito,
                    municipio=municipios[i],
                    papel='prefeito',
                    defaults={
                        'inicio_mandato': date(2025, 1, 1),
                        'fim_mandato': date(2028, 12, 31),
                        'vigente': True,
                    },
                )
        # Secretários e assessores vinculados a municípios aleatórios
        outros = [p for p in pessoas if p.tipo in ('secretario', 'assessor')]
        for pessoa in outros:
            mun = random.choice(municipios[:10])
            VinculoMunicipio.objects.get_or_create(
                pessoa=pessoa,
                municipio=mun,
                papel=pessoa.tipo,
                defaults={
                    'inicio_mandato': date(2025, 1, 1),
                    'vigente': True,
                },
            )
        self.stdout.write('  Vínculos criados')

        # Adimplência (2025 e 2026)
        for mun in municipios:
            for ano in [2025, 2026]:
                if mun.associado_fnp:
                    status = random.choices(
                        ['adimplente', 'inadimplente', 'parcial'],
                        weights=[60, 20, 20],
                    )[0]
                    valor_devido = Decimal(random.randint(15000, 80000))
                    if status == 'adimplente':
                        valor_pago = valor_devido
                    elif status == 'parcial':
                        valor_pago = valor_devido * Decimal('0.5')
                    else:
                        valor_pago = Decimal(0)
                else:
                    status = 'inadimplente'
                    valor_devido = Decimal(random.randint(10000, 30000))
                    valor_pago = Decimal(0)

                Adimplencia.objects.get_or_create(
                    municipio=mun,
                    ano_referencia=ano,
                    defaults={
                        'status': status,
                        'valor_devido': valor_devido,
                        'valor_pago': valor_pago,
                        'data_pagamento': date(ano, random.randint(1, 6), 15) if valor_pago > 0 else None,
                    },
                )
        self.stdout.write('  Adimplência criada')

        # Eventos
        eventos = []
        for titulo, tipo, modalidade, inicio, fim, local in EVENTOS_FICTICIOS:
            dt_fim = date.fromisoformat(fim) if fim else None
            ev, _ = Evento.objects.get_or_create(
                titulo=titulo,
                defaults={
                    'tipo': tipo,
                    'modalidade': modalidade,
                    'data_inicio': date.fromisoformat(inicio),
                    'data_fim': dt_fim,
                    'local': local,
                },
            )
            eventos.append(ev)
        self.stdout.write(f'  {len(eventos)} eventos criados/existentes')

        # Participações
        participacoes_criadas = 0
        for evento in eventos:
            n_participantes = random.randint(4, min(12, len(prefeitos)))
            participantes = random.sample(prefeitos, n_participantes)
            for prefeito in participantes:
                vinculo = prefeito.vinculos.filter(vigente=True).first()
                if not vinculo:
                    continue
                forma = 'presencial' if evento.modalidade in ('presencial', 'hibrido') else 'online'
                if evento.modalidade == 'hibrido':
                    forma = random.choice(['presencial', 'online'])
                papel = random.choices(
                    ['participante', 'palestrante', 'organizador', 'moderador'],
                    weights=[70, 15, 10, 5],
                )[0]
                _, created = Participacao.objects.get_or_create(
                    pessoa=prefeito,
                    evento=evento,
                    defaults={
                        'municipio': vinculo.municipio,
                        'forma_participacao': forma,
                        'papel_no_evento': papel,
                        'confirmado': True,
                        'data_confirmacao': timezone.now(),
                    },
                )
                if created:
                    participacoes_criadas += 1
        self.stdout.write(f'  {participacoes_criadas} participações criadas')

        # Engajamento — recalcular para cada município associado
        config = ConfiguracaoEngajamento.atual()
        for mun in municipios:
            if mun.associado_fnp:
                eng, _ = Engajamento.objects.get_or_create(
                    municipio=mun,
                    bienio=config.bienio_atual,
                )
                eng.recalcular()
        self.stdout.write('  Engajamento recalculado')

        self.stdout.write(self.style.SUCCESS('\nMockup criado com sucesso!'))
