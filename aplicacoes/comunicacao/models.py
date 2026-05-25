"""Models de Comunicação — templates de e-mail por categoria e registro de envios.

A FNP precisa enviar e-mails em massa para participantes/representantes de
cada categoria (Instâncias, Projetos, Missões, Atividades, Eventos). O
``TemplateEmail`` armazena assunto + corpo padrão por categoria, e o
``Envio`` registra cada disparo realizado (auditoria + idempotência futura).
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from aplicacoes.nucleo.models import ModeloBase
from aplicacoes.nucleo.validators import validar_anexo_seguro


class TemplateEmail(ModeloBase):
    """Modelo de e-mail reutilizável, agrupado por categoria do sistema.

    Suporta placeholders Django via ``{{ }}`` no corpo e assunto:
    - ``{{ entidade }}``: representação textual da entidade-fonte
    - ``{{ pessoa }}``: nome do destinatário
    - ``{{ municipio }}``: município vinculado ao destinatário, se houver

    O conteúdo é renderizado com ``django.template.Template`` na hora do envio.
    """

    class Categoria(models.TextChoices):
        INSTANCIAS = 'instancias', 'Espaços de Diálogo'
        PROJETOS = 'projetos', 'Projetos'
        MISSOES = 'missoes', 'Missões'
        ATIVIDADES = 'atividades', 'Atividades'
        EVENTOS = 'eventos', 'Eventos'
        GERAL = 'geral', 'Geral / Outros'

    nome = models.CharField('nome do template', max_length=200)
    categoria = models.CharField(
        'categoria',
        max_length=15,
        choices=Categoria.choices,
        default=Categoria.GERAL,
        help_text='Em que categoria do sistema este template fica disponível.',
    )
    assunto = models.CharField(
        'assunto',
        max_length=255,
        help_text='Aceita placeholders: {{ entidade }}, {{ pessoa }}, {{ municipio }}',
    )
    corpo = models.TextField(
        'corpo do e-mail',
        help_text='Aceita placeholders: {{ entidade }}, {{ pessoa }}, {{ municipio }}.',
    )
    ativo = models.BooleanField('ativo?', default=True)
    descricao = models.TextField(
        'descrição interna',
        blank=True,
        help_text='Quando usar este template, observações internas.',
    )

    class Meta:
        verbose_name = 'template de e-mail'
        verbose_name_plural = 'templates de e-mail'
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f'{self.nome} ({self.get_categoria_display()})'


class Envio(ModeloBase):
    """Registro de um envio de e-mail em massa a partir de uma entidade.

    Cada envio fica associado à entidade de origem (via GenericForeignKey),
    ao template usado e a quem disparou. Os destinatários são gravados em JSON
    para preservar a fotografia exata do envio.
    """

    class StatusEnvio(models.TextChoices):
        ENVIADO = 'enviado', 'Enviado'
        FALHA = 'falha', 'Falha'
        PARCIAL = 'parcial', 'Parcial (alguns destinatários falharam)'

    class Canal(models.TextChoices):
        EMAIL = 'email', 'E-mail'
        WHATSAPP = 'whatsapp', 'WhatsApp (link wa.me)'
        AMBOS = 'ambos', 'E-mail + WhatsApp'

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='tipo da entidade',
    )
    object_id = models.UUIDField('id do objeto')
    entidade = GenericForeignKey('content_type', 'object_id')

    template = models.ForeignKey(
        TemplateEmail,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='envios',
        verbose_name='template usado',
    )
    assunto = models.CharField(
        'assunto enviado',
        max_length=255,
        help_text='Snapshot do assunto na hora do envio (sem placeholders).',
    )
    corpo = models.TextField(
        'corpo enviado',
        help_text='Snapshot do corpo (sem placeholders) — para auditoria.',
    )
    destinatarios = models.JSONField(
        'destinatários',
        default=list,
        help_text='Lista de e-mails efetivamente disparados (snapshot).',
    )
    total_destinatarios = models.PositiveIntegerField('total de destinatários', default=0)
    status = models.CharField(
        'status',
        max_length=10,
        choices=StatusEnvio.choices,
        default=StatusEnvio.ENVIADO,
    )
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='envios_realizados',
        verbose_name='enviado por',
    )
    erro = models.TextField('mensagem de erro', blank=True)
    anexo = models.FileField(
        'anexo',
        upload_to='envios/%Y/%m/',
        blank=True,
        null=True,
        validators=[validar_anexo_seguro],
        help_text='Arquivo opcional anexado ao envio (máx. 25 MB, executáveis bloqueados).',
    )
    canal = models.CharField(
        'canal de envio',
        max_length=10,
        choices=Canal.choices,
        default=Canal.EMAIL,
        help_text='WhatsApp gera links wa.me (cliquei e envio manual); e-mail envia via SMTP.',
    )
    links_whatsapp = models.JSONField(
        'links wa.me gerados',
        default=list,
        blank=True,
        help_text='Lista de URLs wa.me prontas para o usuário clicar e disparar a mensagem.',
    )

    class Meta:
        verbose_name = 'envio de e-mail'
        verbose_name_plural = 'envios de e-mail'
        ordering = ['-criado_em']
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return f'{self.assunto} — {self.total_destinatarios} destinatários'
