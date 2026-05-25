"""Comando de purga LGPD — elimina dados além do período de retenção.

Política de retenção padrão:
- LogAlteracao: 730 dias (2 anos) — auditoria interna
- Envio (mala direta): 1825 dias (5 anos) — prestação de contas
- Visita à FNP: 1825 dias (5 anos) — controle de acesso
- CredenciamentoPrevio expirado/usado: 365 dias (1 ano)
- SolicitacaoExclusao atendida: 1825 dias (5 anos, para fiscalização ANPD)

Uso: ``python manage.py purgar_dados_antigos [--dry-run]``

O comando é idempotente: roda quantas vezes precisar sem efeitos colaterais.
Sempre rodar com ``--dry-run`` primeiro em produção para auditar quantidades.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Elimina registros pessoais além do período de retenção (LGPD Art. 16).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Apenas reporta o que seria excluído, sem deletar nada.',
        )

    def handle(self, *args, **opts):
        dry_run = opts['dry_run']
        agora = timezone.now()

        # Tabela de políticas: (descrição, queryset_callable, dias)
        from aplicacoes.comunicacao.models import Envio
        from aplicacoes.nucleo.models import LogAlteracao, SolicitacaoExclusao
        from aplicacoes.presenca.models import CredenciamentoPrevio, Visita

        politicas = [
            ('LogAlteracao', lambda d: LogAlteracao.objects.filter(data__lt=d), 730),
            ('Envio', lambda d: Envio.objects.filter(criado_em__lt=d), 1825),
            ('Visita', lambda d: Visita.objects.filter(chegou_em__lt=d), 1825),
            ('CredenciamentoPrevio expirado/usado',
             lambda d: CredenciamentoPrevio.objects.filter(criado_em__lt=d, status__in=['utilizado', 'expirado']),
             365),
            ('SolicitacaoExclusao atendida',
             lambda d: SolicitacaoExclusao.objects.filter(atendido_em__lt=d, status='atendida'),
             1825),
        ]

        total_geral = 0
        for nome, qs_factory, dias in politicas:
            limite = agora - timedelta(days=dias)
            qs = qs_factory(limite)
            count = qs.count()
            total_geral += count
            if count == 0:
                self.stdout.write(f'  {nome}: nada a purgar (>{dias} dias)')
                continue
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'  [DRY-RUN] {nome}: {count} registros seriam excluidos (>{dias} dias)'
                ))
            else:
                deletados, _ = qs.delete()
                self.stdout.write(self.style.SUCCESS(
                    f'  {nome}: {deletados} registros excluidos (>{dias} dias)'
                ))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nTotal que seria purgado: {total_geral}. Rode sem --dry-run para aplicar.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nPurga concluida. Total: {total_geral} registros eliminados.'
            ))
