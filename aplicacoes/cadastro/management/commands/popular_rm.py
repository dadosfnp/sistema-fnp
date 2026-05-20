"""Popula o campo regiao_metropolitana das principais RMs brasileiras.

Lista curada das maiores RMs por codigo IBGE. Roda apos popular_mapa_brasil.
Idempotente — so atualiza municipios ja existentes.
"""

from django.core.management.base import BaseCommand

from aplicacoes.cadastro.models import Municipio


# codigo_ibge -> nome_RM
RMS = {
    # RM de Sao Paulo
    3550308: 'RM de São Paulo', 3548708: 'RM de São Paulo',
    3547809: 'RM de São Paulo', 3518800: 'RM de São Paulo',
    3527207: 'RM de São Paulo', 3530607: 'RM de São Paulo',
    # RM do Rio de Janeiro
    3304557: 'RM do Rio de Janeiro', 3303302: 'RM do Rio de Janeiro',
    3302007: 'RM do Rio de Janeiro', 3304904: 'RM do Rio de Janeiro',
    3300456: 'RM do Rio de Janeiro', 3303609: 'RM do Rio de Janeiro',
    # RM de Belo Horizonte
    3106200: 'RM de Belo Horizonte', 3118601: 'RM de Belo Horizonte',
    # RM de Curitiba
    4106902: 'RM de Curitiba',
    # RM de Porto Alegre
    4314902: 'RM de Porto Alegre', 4313409: 'RM de Porto Alegre',
    4308201: 'RM de Porto Alegre', 4309209: 'RM de Porto Alegre',
    4318705: 'RM de Porto Alegre',
    # RM de Salvador
    2927408: 'RM de Salvador',
    # RM de Recife
    2611606: 'RM de Recife', 2613404: 'RM de Recife',
    2611101: 'RM de Recife (e Petrolina)',
    # RM de Fortaleza
    2304400: 'RM de Fortaleza',
    # RM de Belem
    1501402: 'RM de Belém',
    # RM de Goiania
    5208707: 'RM de Goiânia', 5208400: 'RM de Goiânia',
    # RM de Campinas
    3509502: 'RM de Campinas',
    # RM de Florianopolis
    4205407: 'RM de Florianópolis', 4216602: 'RM de Florianópolis',
    # RM da Grande Vitoria
    3205309: 'RM da Grande Vitória', 3205200: 'RM da Grande Vitória',
    3205002: 'RM da Grande Vitória',
    # RM de Manaus
    1302603: 'RM de Manaus',
    # RIDE-DF
    5300108: 'RIDE Brasília',
    # RM de Aracaju
    2800308: 'RM de Aracaju',
    # RM de Maceio
    2704302: 'RM de Maceió',
    # RM de Joao Pessoa
    2507507: 'RM de João Pessoa',
    # RM de Natal
    2408102: 'RM de Natal',
    # RM de Sao Luis
    2111300: 'RM da Grande São Luís',
    # RM de Teresina
    2211001: 'RM de Teresina',
    # RM de Cuiaba
    5103403: 'RM de Cuiabá', 5103601: 'RM de Cuiabá',
    # RM de Campo Grande
    5002704: 'RM de Campo Grande',
}


class Command(BaseCommand):
    help = 'Popula a regiao_metropolitana dos principais municipios.'

    def handle(self, *args, **opts):
        atualizados = 0
        for codigo, rm in RMS.items():
            n = Municipio.objects.filter(codigo_ibge=codigo).update(regiao_metropolitana=rm)
            atualizados += n
        self.stdout.write(self.style.SUCCESS(
            f'{atualizados} municípios atualizados com região metropolitana.'
        ))
