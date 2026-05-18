"""Comando que congela o engajamento atual em snapshot historico.

Roda no fim de cada bienio para preservar a foto antes do reset/proximo periodo.

Uso:
    python manage.py snapshot_engajamento --bienio=2025-2026
"""

from datetime import date

from django.core.management.base import BaseCommand

from aplicacoes.engajamento.models import Engajamento, SnapshotEngajamento


class Command(BaseCommand):
    help = 'Cria snapshot historico do engajamento de um bienio.'

    def add_arguments(self, parser):
        parser.add_argument('--bienio', required=True, help='Bienio a congelar (ex: 2025-2026)')
        parser.add_argument('--sobrescrever', action='store_true',
                            help='Re-cria snapshots existentes do bienio.')

    def handle(self, *args, **opts):
        bienio = opts['bienio']
        engs = Engajamento.objects.filter(bienio=bienio).select_related('municipio')
        total = engs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING(f'Nenhum engajamento no bienio {bienio}.'))
            return

        if opts['sobrescrever']:
            SnapshotEngajamento.objects.filter(bienio=bienio).delete()

        criados, ignorados = 0, 0
        for e in engs:
            snap, novo = SnapshotEngajamento.objects.get_or_create(
                municipio=e.municipio, bienio=bienio,
                defaults={
                    'pontuacao_bruta': e.pontuacao_bruta,
                    'pontuacao_normalizada': e.pontuacao_normalizada,
                    'nivel': e.nivel,
                    'total_participacoes': e.total_participacoes,
                    'data_snapshot': date.today(),
                },
            )
            if novo:
                criados += 1
            else:
                ignorados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Snapshot do bienio {bienio}: {criados} criados, {ignorados} ja existentes (use --sobrescrever).'
        ))
