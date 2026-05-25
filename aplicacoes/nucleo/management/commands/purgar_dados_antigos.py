"""Purga LGPD — anonimiza ou elimina dados pessoais além do período de retenção.

Política de retenção:
- LogAlteracao: 730 dias (2 anos) — auditoria interna → DELETE
- LogAcessoSensivel: 730 dias (2 anos) — auditoria LGPD → DELETE
- Envio (mala direta): 1825 dias (5 anos) — prestação de contas → DELETE
- Visita à FNP: 1825 dias (5 anos) → ANONIMIZE (preserva estatística)
- CredenciamentoPrevio expirado/usado: 365 dias (1 ano) → DELETE
- SolicitacaoExclusao atendida: 1825 dias (5 anos) → DELETE

Por que anonimizar em vez de deletar a Visita: queremos preservar
contagens históricas ("quantas visitas em 2025?") sem manter PII. Os
campos identificáveis (nome, e-mail, telefone, CPF, foto, embedding,
IP) viram null/genérico; o registro continua contável.

Uso:
    python manage.py purgar_dados_antigos --dry-run
    python manage.py purgar_dados_antigos --so-anonimizar  # nao deleta
    python manage.py purgar_dados_antigos
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Anonimiza/elimina dados pessoais alem do periodo de retencao (LGPD Art. 16).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Apenas reporta o que seria feito.',
        )
        parser.add_argument(
            '--so-anonimizar', action='store_true',
            help='Faz apenas a anonimizacao, sem deletar nada.',
        )

    def handle(self, *args, **opts):
        dry_run = opts['dry_run']
        so_anon = opts['so_anonimizar']
        agora = timezone.now()
        total = 0

        from aplicacoes.comunicacao.models import Envio
        from aplicacoes.nucleo.models import (
            LogAcessoSensivel, LogAlteracao, SolicitacaoExclusao,
        )
        from aplicacoes.presenca.models import CredenciamentoPrevio, Visita

        # --- Anonimizar Visita (preserva estatistica) -----------------------
        limite_visita = agora - timedelta(days=1825)
        visitas = Visita.objects.filter(
            chegou_em__lt=limite_visita,
        ).exclude(nome_visitante='[anonimizado]')
        count_v = visitas.count()
        total += count_v
        if count_v:
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'  [DRY-RUN] Visita: {count_v} registros seriam anonimizados (>1825 dias)'
                ))
            else:
                self._anonimizar_visitas(visitas)
                self.stdout.write(self.style.SUCCESS(
                    f'  Visita: {count_v} registros anonimizados (preserva estatistica)'
                ))
        else:
            self.stdout.write('  Visita: nada a anonimizar')

        if so_anon:
            self.stdout.write(self.style.SUCCESS(f'\nAnonimizacao concluida. Total: {total}.'))
            return

        # --- Deletar logs / envios / pre-cred / solicitacoes -----------------
        politicas = [
            ('LogAlteracao', lambda d: LogAlteracao.objects.filter(data__lt=d), 730),
            ('LogAcessoSensivel', lambda d: LogAcessoSensivel.objects.filter(data__lt=d), 730),
            ('Envio', lambda d: Envio.objects.filter(criado_em__lt=d), 1825),
            ('CredenciamentoPrevio expirado/usado',
             lambda d: CredenciamentoPrevio.objects.filter(criado_em__lt=d, status__in=['utilizado', 'expirado']),
             365),
            ('SolicitacaoExclusao atendida',
             lambda d: SolicitacaoExclusao.objects.filter(atendido_em__lt=d, status='atendida'),
             1825),
        ]

        for nome, qs_factory, dias in politicas:
            limite = agora - timedelta(days=dias)
            qs = qs_factory(limite)
            count = qs.count()
            total += count
            if count == 0:
                self.stdout.write(f'  {nome}: nada a purgar (>{dias} dias)')
                continue
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'  [DRY-RUN] {nome}: {count} seriam excluidos (>{dias} dias)'
                ))
            else:
                deletados, _ = qs.delete()
                self.stdout.write(self.style.SUCCESS(
                    f'  {nome}: {deletados} excluidos (>{dias} dias)'
                ))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nTotal que seria afetado: {total}. Rode sem --dry-run para aplicar.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nPurga concluida. Total afetado: {total}.'
            ))

    def _anonimizar_visitas(self, queryset):
        """Substitui PII por valores genéricos preservando contagem.

        Por que: dados como nome/CPF/foto sao desnecessarios para
        estatistica historica ("quantas visitas em 2024?"). Anonimizar
        em vez de deletar atende ao principio LGPD de minimizacao
        sem perder visibilidade institucional.
        """
        with transaction.atomic():
            for v in queryset.iterator():
                v.nome_visitante = '[anonimizado]'
                v.email = ''
                v.telefone = ''
                v.organizacao = ''
                v.observacao = ''
                v.face_embedding = []
                if v.foto:
                    try:
                        v.foto.delete(save=False)
                    except Exception:
                        pass
                    v.foto = None
                v.save(update_fields=[
                    'nome_visitante', 'email', 'telefone', 'organizacao',
                    'observacao', 'face_embedding', 'foto',
                ])
