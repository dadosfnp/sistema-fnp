"""Signals genéricos: auditoria + dispatcher de webhooks.

Conectados a ``pre_delete`` (auditoria) e ``post_save`` (webhooks externos)
de modelos específicos do dominio.
"""

from django.db.models.signals import post_save, pre_delete
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


def _disparar_webhook_seguro(tipo, dados):
    """Wrapper que ignora erros do dispatcher — webhooks nunca derrubam signals."""
    try:
        from aplicacoes.nucleo.servicos.webhooks import disparar
        disparar(tipo, dados)
    except Exception:
        pass


def conectar_signals_webhooks():
    """Liga signals que disparam webhooks. Chamado em NucleoConfig.ready."""
    from aplicacoes.adimplencia.models import Adimplencia
    from aplicacoes.atividades.models import Atividade
    from aplicacoes.cadastro.models import Pessoa
    from aplicacoes.eventos.models import Evento
    from aplicacoes.missoes.models import Missao

    def _adim(sender, instance, created, **kwargs):
        _disparar_webhook_seguro('municipio.adimplencia_mudou', {
            'municipio_id': str(instance.municipio_id),
            'municipio_nome': instance.municipio.nome,
            'status': instance.status,
            'ano_referencia': instance.ano_referencia,
        })

    def _evento(sender, instance, created, **kwargs):
        if created:
            _disparar_webhook_seguro('evento.criado', {
                'evento_id': str(instance.pk),
                'titulo': instance.titulo,
                'data_inicio': instance.data_inicio.isoformat(),
                'tipo': instance.tipo,
            })

    def _atividade(sender, instance, created, **kwargs):
        if instance.status == 'realizada':
            _disparar_webhook_seguro('atividade.realizada', {
                'atividade_id': str(instance.pk),
                'titulo': instance.titulo,
                'instancia_id': str(instance.instancia_id),
            })

    def _missao(sender, instance, created, **kwargs):
        if instance.status in ('concluida', 'encerrada'):
            _disparar_webhook_seguro('missao.encerrada', {
                'missao_id': str(instance.pk),
                'titulo': instance.titulo,
            })

    def _pessoa(sender, instance, created, **kwargs):
        if created:
            _disparar_webhook_seguro('pessoa.cadastrada', {
                'pessoa_id': str(instance.pk),
                'nome': instance.nome,
                'tipo': instance.tipo,
            })

    post_save.connect(_adim, sender=Adimplencia, weak=False)
    post_save.connect(_evento, sender=Evento, weak=False)
    post_save.connect(_atividade, sender=Atividade, weak=False)
    post_save.connect(_missao, sender=Missao, weak=False)
    post_save.connect(_pessoa, sender=Pessoa, weak=False)
