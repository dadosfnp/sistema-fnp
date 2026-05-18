"""Model de Documento universal, anexável a qualquer entidade via GenericForeignKey.

Permite que Instâncias, Projetos, Missões, Atividades, Eventos e outras
entidades tenham seu próprio repositório de documentos sem duplicar a tabela
para cada tipo. A relação inversa fica acessível via ``obj.documentos.all()``
quando o model define um ``GenericRelation``.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from aplicacoes.nucleo.models import ModeloBase


class Documento(ModeloBase):
    """Arquivo anexado a uma entidade qualquer do sistema.

    O par ``content_type`` + ``object_id`` aponta para a entidade dona do
    documento (Instância, Projeto, Missão, Atividade, Evento etc.).
    ``tipo`` permite filtrar por categoria de documento (pauta, ata,
    apresentação...) e padronizar relatórios.
    """

    class TipoDocumento(models.TextChoices):
        PAUTA = 'pauta', 'Pauta'
        ATA = 'ata', 'Ata'
        PROGRAMACAO = 'programacao', 'Programação'
        LISTA_PRESENCA = 'lista_presenca', 'Lista de presença'
        APRESENTACAO = 'apresentacao', 'Apresentação'
        RELATORIO = 'relatorio', 'Relatório'
        CERTIFICADO = 'certificado', 'Certificado'
        OFICIO = 'oficio', 'Ofício'
        TERMO = 'termo', 'Termo'
        DECRETO_LEI = 'decreto_lei', 'Decreto / Lei / Portaria'
        FOTO = 'foto', 'Foto'
        OUTRO = 'outro', 'Outro'

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='tipo da entidade',
    )
    object_id = models.UUIDField(
        'id do objeto',
        help_text='UUID do objeto referenciado (Instância, Projeto, Missão etc.).',
    )
    entidade = GenericForeignKey('content_type', 'object_id')

    nome = models.CharField(
        'nome do documento',
        max_length=255,
        help_text='Título descritivo do documento (ex.: "Ata reunião 12/03/2026").',
    )
    tipo = models.CharField(
        'tipo de documento',
        max_length=20,
        choices=TipoDocumento.choices,
        default=TipoDocumento.OUTRO,
    )
    arquivo = models.FileField(
        'arquivo',
        upload_to='documentos/%Y/%m/',
        blank=True,
        null=True,
        help_text='Arquivo PDF, imagem ou documento de texto.',
    )
    link_externo = models.URLField(
        'link externo',
        blank=True,
        help_text='Alternativa ao upload — URL para o documento hospedado externamente.',
    )
    descricao = models.TextField('descrição', blank=True)
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_enviados',
        verbose_name='enviado por',
    )

    class Meta:
        verbose_name = 'documento'
        verbose_name_plural = 'documentos'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()}: {self.nome}'

    @property
    def url(self):
        """URL pública do documento: arquivo enviado ou link externo."""
        if self.arquivo:
            return self.arquivo.url
        return self.link_externo or ''
