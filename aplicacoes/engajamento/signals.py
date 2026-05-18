"""Signals para recálculo automático de engajamento.

Quando qualquer fonte de pontos muda — participação, adimplência, representação,
presença em atividade, membro de delegação — o engajamento do(s) município(s)
afetado(s) é recalculado. Mantém o score em sincronia sem comando manual.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


def _recalcular_engajamento_municipio(municipio):
    """Obtém ou cria o Engajamento do município no biênio atual e dispara recálculo."""
    from aplicacoes.engajamento.models import ConfiguracaoEngajamento, Engajamento
    if not municipio:
        return
    config = ConfiguracaoEngajamento.atual()
    engajamento, _ = Engajamento.objects.get_or_create(
        municipio=municipio, bienio=config.bienio_atual,
    )
    engajamento.recalcular()


def _municipios_da_pessoa(pessoa):
    """Lista municípios em que a pessoa tem vínculo vigente."""
    from aplicacoes.cadastro.models import Municipio
    if not pessoa:
        return Municipio.objects.none()
    return Municipio.objects.filter(vinculos__pessoa=pessoa, vinculos__vigente=True).distinct()


def _signal_participacao_ou_adimplencia(sender, instance, **kwargs):
    """Recálculo direto para fontes que já têm FK para municipio."""
    _recalcular_engajamento_municipio(getattr(instance, 'municipio', None))


def _signal_via_pessoa(sender, instance, **kwargs):
    """Recálculo amplo para fontes ligadas via pessoa (representação, missão)."""
    for m in _municipios_da_pessoa(getattr(instance, 'pessoa', None)):
        _recalcular_engajamento_municipio(m)


def _signal_via_presenca(sender, instance, **kwargs):
    """Presenca já tem municipio direto na FK."""
    _recalcular_engajamento_municipio(getattr(instance, 'municipio', None))


def conectar_signals():
    """Liga os signals lazily após apps estarem prontos (evita import circular)."""
    from aplicacoes.adimplencia.models import Adimplencia
    from aplicacoes.eventos.models import Participacao
    from aplicacoes.instancias.models import Representacao
    from aplicacoes.missoes.models import MembroDelegacao
    from aplicacoes.presenca.models import Presenca

    for modelo in (Participacao, Adimplencia):
        post_save.connect(_signal_participacao_ou_adimplencia, sender=modelo, weak=False)
        post_delete.connect(_signal_participacao_ou_adimplencia, sender=modelo, weak=False)

    for modelo in (Representacao, MembroDelegacao):
        post_save.connect(_signal_via_pessoa, sender=modelo, weak=False)
        post_delete.connect(_signal_via_pessoa, sender=modelo, weak=False)

    post_save.connect(_signal_via_presenca, sender=Presenca, weak=False)
    post_delete.connect(_signal_via_presenca, sender=Presenca, weak=False)
