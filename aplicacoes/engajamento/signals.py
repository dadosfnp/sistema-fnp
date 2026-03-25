from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.eventos.models import Participacao


def _recalcular_engajamento_municipio(municipio):
    """Recalcula o engajamento do município no biênio atual."""
    from aplicacoes.engajamento.models import ConfiguracaoEngajamento, Engajamento

    config = ConfiguracaoEngajamento.atual()
    engajamento, _ = Engajamento.objects.get_or_create(
        municipio=municipio,
        bienio=config.bienio_atual,
    )
    engajamento.recalcular()


@receiver(post_save, sender=Participacao)
def recalcular_engajamento_ao_salvar_participacao(sender, instance, **kwargs):
    """Recalcula engajamento quando uma participação é salva."""
    _recalcular_engajamento_municipio(instance.municipio)


@receiver(post_delete, sender=Participacao)
def recalcular_engajamento_ao_deletar_participacao(sender, instance, **kwargs):
    """Recalcula engajamento quando uma participação é removida."""
    _recalcular_engajamento_municipio(instance.municipio)


@receiver(post_save, sender=Adimplencia)
def recalcular_engajamento_ao_mudar_adimplencia(sender, instance, **kwargs):
    """Recalcula engajamento quando a adimplência muda (penalidade)."""
    _recalcular_engajamento_municipio(instance.municipio)
