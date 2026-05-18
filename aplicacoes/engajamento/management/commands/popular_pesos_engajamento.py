"""Seed de pesos do engajamento — baseline sugerido pela equipe FNP.

Os valores são pontos de partida; a equipe pode ajustar via admin Unfold
ou rodando este comando novamente após editar a constante ``PESOS``.
"""

from django.core.management.base import BaseCommand

from aplicacoes.engajamento.models import PesoEngajamento


PESOS = [
    ('evento_presencial', 10,
     'Participação presencial em evento institucional (assembleia, congresso, fórum etc.).'),
    ('evento_online', 5,
     'Participação online em evento institucional. Vale metade do presencial.'),
    ('evento_bonus_palestrante', 5,
     'Bônus adicional para quem palestrou no evento.'),
    ('evento_bonus_organizador', 5,
     'Bônus adicional para quem ajudou a organizar o evento.'),
    ('representacao_titular', 20,
     'Representante titular vigente em Espaço de Diálogo Federativo. Pontua enquanto o mandato estiver ativo.'),
    ('representacao_suplente', 10,
     'Representante suplente vigente. Pontua enquanto o mandato estiver ativo.'),
    ('representacao_diretiva', 30,
     'Função diretiva (presidência, vice, secretaria geral/executiva, diretor temático/regional).'),
    ('presenca_atividade', 5,
     'Presença confirmada em atividade (reunião) de uma instância.'),
    ('missao_internacional', 30,
     'Participação em delegação de missão internacional.'),
    ('missao_nacional', 15,
     'Participação em delegação de missão nacional.'),
]


class Command(BaseCommand):
    """Popula/atualiza os pesos do engajamento com os valores baseline."""

    help = 'Cria ou atualiza os pesos de cada categoria no cálculo de engajamento.'

    def handle(self, *args, **options):
        criados = 0
        atualizados = 0
        for chave, peso, descricao in PESOS:
            _, criado = PesoEngajamento.objects.update_or_create(
                chave=chave,
                defaults={'peso': peso, 'descricao': descricao, 'ativo': True},
            )
            if criado:
                criados += 1
            else:
                atualizados += 1
        self.stdout.write(self.style.SUCCESS(
            f'Concluido: {criados} criados, {atualizados} atualizados, {len(PESOS)} total.'
        ))
