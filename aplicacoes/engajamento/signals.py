from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from aplicacoes.eventos.models import Participacao


@receiver(post_save, sender=Participacao)
def atualizar_engajamento_ao_registrar_participacao(sender, instance, created, **kwargs):
    """Recalcula engajamento do município ao registrar participação."""
    if not created:
        return

    pessoa = instance.pessoa
    vinculos = pessoa.vinculos.filter(vigente=True)

    for vinculo in vinculos:
        from aplicacoes.engajamento.models import Engajamento

        engajamento, _ = Engajamento.objects.get_or_create(
            municipio=vinculo.municipio,
        )
        engajamento.pontuacao_total += instance.evento.peso_engajamento
        engajamento.total_participacoes += 1
        engajamento.ultima_interacao = timezone.now()
        engajamento.recalcular_nivel()
        engajamento.save()
