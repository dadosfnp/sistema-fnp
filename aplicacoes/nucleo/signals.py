"""Signals genéricos de auditoria.

Conectados a ``pre_delete`` de toda subclasse de ``ModeloBase`` — cobre
deleções diretas e em cascata, sem precisar instrumentar cada view.
"""

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from aplicacoes.nucleo.models import LogAlteracao, ModeloBase


@receiver(pre_delete)
def auditar_delete_generico(sender, instance, **kwargs):
    """Registra LogAlteracao para qualquer ModeloBase em vias de ser deletado.

    Sem usuário associado (cascade não tem contexto de request). Mesmo assim
    o evento é preservado: data, modelo e objeto_repr garantem rastreabilidade.
    """
    if not isinstance(instance, ModeloBase):
        return
    # Evita auto-loop: o próprio LogAlteracao herda de models.Model, não ModeloBase.
    LogAlteracao.objects.create(
        usuario=None,
        acao=LogAlteracao.TipoAcao.EXCLUSAO,
        modelo=instance.__class__.__name__,
        objeto_id=str(instance.pk),
        objeto_repr=str(instance)[:255],
    )
