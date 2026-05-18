"""Popula o mapa com municipios mockup espalhados pelo Brasil.

Acrescenta ~60 municipios curados (capitais + grandes cidades) com lat/lng
reais e adimplencia/engajamento aleatorios para que o mapa fique visualmente
rico durante demos. Idempotente — nao duplica registros existentes.
"""

import random

from django.core.management.base import BaseCommand

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.cadastro.models import Municipio

# (codigo_ibge, nome, uf, regiao, lat, lng, populacao, eh_capital, associado_fnp)
MUNICIPIOS = [
    # NORTE
    (1100205, 'Porto Velho', 'RO', 'norte', -8.7619, -63.9039, 539354, True, True),
    (1200401, 'Rio Branco', 'AC', 'norte', -9.9747, -67.8243, 419452, True, True),
    (1302603, 'Manaus', 'AM', 'norte', -3.1190, -60.0217, 2255903, True, True),
    (1400100, 'Boa Vista', 'RR', 'norte', 2.8235, -60.6758, 437432, True, True),
    (1501402, 'Belém', 'PA', 'norte', -1.4558, -48.4902, 1303403, True, True),
    (1600303, 'Macapá', 'AP', 'norte', 0.0349, -51.0694, 522357, True, True),
    (1721000, 'Palmas', 'TO', 'norte', -10.1845, -48.3336, 313349, True, True),
    (1501709, 'Santarém', 'PA', 'norte', -2.4380, -54.6996, 308339, False, False),
    # NORDESTE
    (2111300, 'São Luís', 'MA', 'nordeste', -2.5307, -44.3068, 1037590, True, True),
    (2211001, 'Teresina', 'PI', 'nordeste', -5.0892, -42.8019, 884706, True, True),
    (2304400, 'Fortaleza', 'CE', 'nordeste', -3.7172, -38.5433, 2685911, True, True),
    (2408102, 'Natal', 'RN', 'nordeste', -5.7945, -35.2110, 890480, True, True),
    (2507507, 'João Pessoa', 'PB', 'nordeste', -7.1195, -34.8450, 833932, True, True),
    (2611606, 'Recife', 'PE', 'nordeste', -8.0476, -34.8770, 1661017, True, True),
    (2704302, 'Maceió', 'AL', 'nordeste', -9.6498, -35.7089, 1025360, True, True),
    (2800308, 'Aracaju', 'SE', 'nordeste', -10.9472, -37.0731, 664908, True, True),
    (2927408, 'Salvador', 'BA', 'nordeste', -12.9714, -38.5014, 2900319, True, True),
    (2933307, 'Vitória da Conquista', 'BA', 'nordeste', -14.8615, -40.8442, 341128, False, True),
    (2403103, 'Mossoró', 'RN', 'nordeste', -5.1875, -37.3445, 300618, False, False),
    (2607901, 'Olinda', 'PE', 'nordeste', -8.0089, -34.8553, 393115, False, True),
    (2611101, 'Petrolina', 'PE', 'nordeste', -9.3891, -40.5030, 354317, False, False),
    (2914802, 'Feira de Santana', 'BA', 'nordeste', -12.2664, -38.9663, 619609, False, True),
    # CENTRO-OESTE
    (5002704, 'Campo Grande', 'MS', 'centro_oeste', -20.4486, -54.6295, 916001, True, True),
    (5103403, 'Cuiabá', 'MT', 'centro_oeste', -15.6010, -56.0974, 650877, True, True),
    (5208707, 'Goiânia', 'GO', 'centro_oeste', -16.6864, -49.2643, 1555626, True, True),
    (5300108, 'Brasília', 'DF', 'centro_oeste', -15.7801, -47.9292, 3055149, True, True),
    (5208400, 'Anápolis', 'GO', 'centro_oeste', -16.3267, -48.9527, 391772, False, True),
    (5103601, 'Várzea Grande', 'MT', 'centro_oeste', -15.6467, -56.1326, 287818, False, False),
    (5006606, 'Dourados', 'MS', 'centro_oeste', -22.2231, -54.8120, 227949, False, False),
    # SUDESTE
    (3106200, 'Belo Horizonte', 'MG', 'sudeste', -19.9167, -43.9345, 2315560, True, True),
    (3205309, 'Vitória', 'ES', 'sudeste', -20.3155, -40.3128, 322869, True, True),
    (3304557, 'Rio de Janeiro', 'RJ', 'sudeste', -22.9068, -43.1729, 6211423, True, True),
    (3550308, 'São Paulo', 'SP', 'sudeste', -23.5505, -46.6333, 12325232, True, True),
    (3509502, 'Campinas', 'SP', 'sudeste', -22.9099, -47.0626, 1139047, False, True),
    (3543402, 'Ribeirão Preto', 'SP', 'sudeste', -21.1775, -47.8103, 711825, False, True),
    (3548708, 'Santo André', 'SP', 'sudeste', -23.6633, -46.5288, 720964, False, True),
    (3518800, 'Guarulhos', 'SP', 'sudeste', -23.4628, -46.5333, 1392121, False, True),
    (3304904, 'São Gonçalo', 'RJ', 'sudeste', -22.8268, -43.0537, 1098357, False, False),
    (3303302, 'Niterói', 'RJ', 'sudeste', -22.8833, -43.1036, 515317, False, True),
    (3170206, 'Uberlândia', 'MG', 'sudeste', -18.9128, -48.2755, 706597, False, True),
    (3118601, 'Contagem', 'MG', 'sudeste', -19.9314, -44.0536, 668949, False, False),
    (3205200, 'Vila Velha', 'ES', 'sudeste', -20.3297, -40.2925, 491540, False, True),
    (3205002, 'Serra', 'ES', 'sudeste', -20.1281, -40.3078, 527248, False, False),
    (3303500, 'Petrópolis', 'RJ', 'sudeste', -22.5051, -43.1786, 305687, False, False),
    # SUL
    (4106902, 'Curitiba', 'PR', 'sul', -25.4284, -49.2733, 1963726, True, True),
    (4205407, 'Florianópolis', 'SC', 'sul', -27.5954, -48.5480, 508826, True, True),
    (4314902, 'Porto Alegre', 'RS', 'sul', -30.0346, -51.2177, 1488252, True, True),
    (4113700, 'Londrina', 'PR', 'sul', -23.3045, -51.1696, 575377, False, True),
    (4115200, 'Maringá', 'PR', 'sul', -23.4205, -51.9331, 436472, False, True),
    (4119905, 'Ponta Grossa', 'PR', 'sul', -25.0916, -50.1668, 358838, False, False),
    (4209102, 'Joinville', 'SC', 'sul', -26.3045, -48.8487, 597658, False, True),
    (4202404, 'Blumenau', 'SC', 'sul', -26.9156, -49.0688, 366418, False, True),
    (4216602, 'São José', 'SC', 'sul', -27.6109, -48.6336, 250208, False, False),
    (4314407, 'Pelotas', 'RS', 'sul', -31.7654, -52.3371, 343132, False, False),
    (4304606, 'Caxias do Sul', 'RS', 'sul', -29.1685, -51.1796, 517451, False, True),
    (4309209, 'Canoas', 'RS', 'sul', -29.9189, -51.1840, 348208, False, False),
    (4316907, 'Santa Maria', 'RS', 'sul', -29.6842, -53.8069, 281466, False, False),
]


class Command(BaseCommand):
    help = 'Popula ~60 municipios brasileiros com adimplencia mockup para o mapa ficar visual.'

    def add_arguments(self, parser):
        parser.add_argument('--ano', type=int, default=2026,
                            help='Ano de referencia para adimplencia (default 2026).')
        parser.add_argument('--limpar-adimplencia', action='store_true',
                            help='Apaga adimplencias do ano antes de popular.')

    def handle(self, *args, **opts):
        ano = opts['ano']
        criados, atualizados = 0, 0

        for dados in MUNICIPIOS:
            codigo, nome, uf, regiao, lat, lng, pop, capital, assoc = dados
            muni, novo = Municipio.objects.update_or_create(
                codigo_ibge=codigo,
                defaults={
                    'nome': nome, 'uf': uf, 'regiao': regiao,
                    'latitude': lat, 'longitude': lng,
                    'populacao': pop, 'eh_capital': capital, 'associado_fnp': assoc,
                },
            )
            if novo:
                criados += 1
            else:
                atualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Municipios: {criados} criados, {atualizados} atualizados ({len(MUNICIPIOS)} no total).'
        ))

        # Adimplencia mockup — distribuicao realista (60% adim, 25% parcial, 15% inad)
        if opts['limpar_adimplencia']:
            n = Adimplencia.objects.filter(ano_referencia=ano).count()
            Adimplencia.objects.filter(ano_referencia=ano).delete()
            self.stdout.write(self.style.WARNING(f'Removidas {n} adimplencias de {ano}.'))

        random.seed(42)  # reprodutivel
        criadas, ignoradas = 0, 0
        status_choices = (
            ['adimplente'] * 60 + ['parcial'] * 25 + ['inadimplente'] * 15
        )

        for dados in MUNICIPIOS:
            muni = Municipio.objects.get(codigo_ibge=dados[0])
            status = random.choice(status_choices)
            valor_devido = round(muni.populacao * 0.05, 2)
            valor_pago = {
                'adimplente': valor_devido,
                'parcial': round(valor_devido * 0.5, 2),
                'inadimplente': 0,
            }[status]
            _, novo = Adimplencia.objects.get_or_create(
                municipio=muni, ano_referencia=ano,
                defaults={
                    'status': status, 'valor_devido': valor_devido, 'valor_pago': valor_pago,
                },
            )
            if novo:
                criadas += 1
            else:
                ignoradas += 1

        self.stdout.write(self.style.SUCCESS(
            f'Adimplencias {ano}: {criadas} criadas, {ignoradas} ja existentes (use --limpar-adimplencia para refazer).'
        ))
