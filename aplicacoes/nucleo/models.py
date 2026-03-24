import uuid

from django.db import models


class ModeloBase(models.Model):
    """Modelo abstrato base para todos os models do sistema."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    criado_em = models.DateTimeField('criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        abstract = True
