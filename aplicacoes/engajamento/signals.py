"""Signals para recálculo automático de engajamento ao alterar participações ou adimplência."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.eventos.models import Participacao


def _recalcular_engajamento_municipio(municipio):
    """Obtém ou cria o Engajamento do município no biênio atual e dispara recálculo."""
    from aplicacoes.engajamento.models import ConfiguracaoEngajamento, Engajamento

    config = ConfiguracaoEngajamento.atual()
    engajamento, _ = Engajamento.objects.get_or_create(
        municipio=municipio,
        bienio=config.bienio_atual,
    )
    engajamento.recalcular()


@receiver(post_save, sender=Participacao)
def recalcular_engajamento_ao_salvar_participacao(sender, instance, **kwargs):
    """Signal post_save de Participacao — atualiza pontuação do município."""
    _recalcular_engajamento_municipio(instance.municipio)


@receiver(post_delete, sender=Participacao)
def recalcular_engajamento_ao_deletar_participacao(sender, instance, **kwargs):
    """Signal post_delete de Participacao — recalcula pontuação sem a participação removida."""
    _recalcular_engajamento_municipio(instance.municipio)


@receiver(post_save, sender=Adimplencia)
def recalcular_engajamento_ao_mudar_adimplencia(sender, instance, **kwargs):
    """Signal post_save de Adimplencia — reaplica penalidades no engajamento."""
    _recalcular_engajamento_municipio(instance.municipio)
