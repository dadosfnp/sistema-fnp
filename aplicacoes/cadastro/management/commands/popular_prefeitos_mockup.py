"""Atribui prefeitos fictícios com partidos aos municípios para popular filtros.

Cria Pessoa(tipo=prefeito) + VinculoMunicipio(papel=prefeito, vigente=True)
para cada município que ainda não tenha. Partido distribuído proporcionalmente
aos partidos reais brasileiros (2026 aproximado).
"""

import random

from django.core.management.base import BaseCommand

from aplicacoes.cadastro.models import Municipio, Pessoa, VinculoMunicipio

# Partido -> peso (proporcional a real). PSD/MDB/PP dominam.
DISTRIBUICAO_PARTIDOS = (
    ['PSD'] * 16 + ['MDB'] * 15 + ['PP'] * 13 + ['UNIÃO'] * 11
    + ['REPUBLICANOS'] * 8 + ['PL'] * 9 + ['PT'] * 5 + ['PSB'] * 6
    + ['PSDB'] * 5 + ['PDT'] * 3 + ['PODE'] * 3 + ['CIDADANIA'] * 2
    + ['SOLIDARIEDADE'] * 2 + ['AGIR'] * 1 + ['AVANTE'] * 1
)

# Nomes fictícios — 200 combinações
PRIMEIRO = ['Ana', 'Carlos', 'Maria', 'João', 'Paula', 'Rafael', 'Beatriz',
            'Pedro', 'Juliana', 'Antônio', 'Sofia', 'Lucas', 'Camila',
            'Eduardo', 'Mariana', 'Fernando', 'Letícia', 'Marcelo', 'Patrícia',
            'Roberto', 'Daniela', 'Marcos', 'Renata', 'André', 'Cristina']
SOBRENOME = ['Silva', 'Souza', 'Oliveira', 'Santos', 'Pereira', 'Lima',
             'Costa', 'Almeida', 'Ferreira', 'Carvalho', 'Ribeiro', 'Martins',
             'Gomes', 'Barbosa', 'Rocha', 'Dias', 'Cardoso', 'Teixeira']


class Command(BaseCommand):
    help = 'Cria prefeitos fictícios com partido para municípios sem prefeito vinculado.'

    def handle(self, *args, **opts):
        random.seed(7)
        novos_prefeitos = 0
        municipios_sem_prefeito = [
            m for m in Municipio.objects.all()
            if not m.vinculos.filter(papel='prefeito', vigente=True).exists()
        ]
        self.stdout.write(f'{len(municipios_sem_prefeito)} municípios sem prefeito vinculado.')

        for m in municipios_sem_prefeito:
            partido = random.choice(DISTRIBUICAO_PARTIDOS)
            nome = f'{random.choice(PRIMEIRO)} {random.choice(SOBRENOME)}'
            pessoa = Pessoa.objects.create(
                nome=nome,
                tipo=Pessoa.TipoPessoa.PREFEITO,
                partido=partido,
                cargo='Prefeito(a)',
            )
            VinculoMunicipio.objects.create(
                pessoa=pessoa, municipio=m,
                papel=VinculoMunicipio.Papel.PREFEITO,
                vigente=True,
            )
            novos_prefeitos += 1

        self.stdout.write(self.style.SUCCESS(
            f'{novos_prefeitos} prefeitos fictícios criados com partido.'
        ))
