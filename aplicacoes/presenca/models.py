"""Model de Presença universal — anexável a qualquer entidade via GenericForeignKey.

Permite registrar quem participou (ou faltou) em Atividades, Eventos, Missões
ou qualquer outra entidade que faça sentido controlar presença. O município é
gravado como snapshot na hora do registro — preserva o vínculo da pessoa ao
município mesmo que ela mude de cargo posteriormente.

Convive com ``eventos.Participacao`` (que mantém pontuação de engajamento) e
``missoes.MembroDelegacao`` (que detalha papéis na delegação) — não os
substitui, complementa: representa o ato simples de "presença".
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.nucleo.models import ModeloBase


class Presenca(ModeloBase):
    """Registro de presença/ausência de uma pessoa em uma entidade qualquer.

    O par ``content_type`` + ``object_id`` aponta para a entidade onde a
    presença ocorreu (Atividade, Evento, Missão etc.). ``municipio`` é um
    snapshot no momento do registro — não muda se o vínculo da pessoa
    posteriormente trocar.
    """

    class Status(models.TextChoices):
        PRESENTE = 'presente', 'Presente'
        AUSENTE = 'ausente', 'Ausente'
        JUSTIFICADA = 'justificada', 'Falta justificada'
        EM_TRANSITO = 'em_transito', 'Em trânsito / parcial'

    class Forma(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        ONLINE = 'online', 'Online'
        HIBRIDO = 'hibrido', 'Híbrido'

    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name='presencas',
        verbose_name='pessoa',
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='tipo da entidade',
    )
    object_id = models.UUIDField('id do objeto')
    entidade = GenericForeignKey('content_type', 'object_id')

    status = models.CharField(
        'status',
        max_length=15,
        choices=Status.choices,
        default=Status.PRESENTE,
    )
    forma = models.CharField(
        'forma de participação',
        max_length=12,
        choices=Forma.choices,
        default=Forma.PRESENCIAL,
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presencas',
        verbose_name='município (snapshot)',
        help_text='Município vinculado à pessoa no momento do registro.',
    )
    observacao = models.TextField('observação', blank=True)
    registrado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presencas_registradas',
        verbose_name='registrado por',
    )

    class Meta:
        verbose_name = 'presença'
        verbose_name_plural = 'presenças'
        ordering = ['-criado_em']
        unique_together = ['pessoa', 'content_type', 'object_id']
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return f'{self.pessoa} — {self.get_status_display()} em {self.entidade}'

    def save(self, *args, **kwargs):
        """Captura snapshot do município vigente da pessoa se ainda não preenchido."""
        if not self.municipio_id and self.pessoa_id:
            vinculo = self.pessoa.vinculos.filter(vigente=True).first()
            if vinculo:
                self.municipio = vinculo.municipio
        super().save(*args, **kwargs)


class Visita(ModeloBase):
    """Visita à sede da FNP registrada pela recepção/secretaria.

    Captura o fluxo simples de "alguém chegou aqui agora" — útil para:
    - Atendimento na recepção (cadastro rápido de quem chega)
    - Histórico de quem passou pela FNP em data X
    - Métrica de visitantes por dia/semana/mês
    - Cruzamento com eventos do dia (se houver)

    Diferente de ``Presenca`` (que aponta para uma entidade específica via
    GenericForeignKey), uma Visita é autônoma — basta nome + horário para
    registrar. Pode opcionalmente referenciar uma pessoa cadastrada e o
    evento/atividade que motivou a visita.
    """

    class Motivo(models.TextChoices):
        REUNIAO = 'reuniao', 'Reunião agendada'
        EVENTO = 'evento', 'Participar de evento/atividade'
        ENTREGA = 'entrega', 'Entrega de documento'
        TECNICO = 'tecnico', 'Atendimento técnico'
        VISITA_INSTITUCIONAL = 'institucional', 'Visita institucional'
        OUTRO = 'outro', 'Outro'

    # Pessoa cadastrada (opcional — se já existe, link; senão captura nome livre)
    pessoa = models.ForeignKey(
        Pessoa, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visitas',
        help_text='Vincular a uma pessoa cadastrada se já existir.',
    )
    nome_visitante = models.CharField(
        'nome do visitante', max_length=255,
        help_text='Preenchido manualmente quando o visitante não tem cadastro.',
    )
    email = models.EmailField('e-mail', blank=True)
    telefone = models.CharField('telefone', max_length=20, blank=True)
    organizacao = models.CharField(
        'organização/cargo', max_length=255, blank=True,
        help_text='Empresa, prefeitura, secretaria etc.',
    )

    motivo = models.CharField(
        'motivo', max_length=20, choices=Motivo.choices, default=Motivo.OUTRO,
    )
    pessoa_recebida_por = models.CharField(
        'recebido(a) por', max_length=255, blank=True,
        help_text='Quem na FNP irá atender (livre — ex.: "Eq. Presidência").',
    )
    observacao = models.TextField('observação', blank=True)

    # Snapshot do município, se houver
    municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='visitas',
        help_text='Município que o visitante representa (se aplicável).',
    )

    chegou_em = models.DateTimeField('chegou em', auto_now_add=True)
    saiu_em = models.DateTimeField('saiu em', null=True, blank=True)
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visitas_registradas',
    )

    class Meta:
        verbose_name = 'visita à FNP'
        verbose_name_plural = 'visitas à FNP'
        ordering = ['-chegou_em']
        indexes = [
            models.Index(fields=['-chegou_em']),
            models.Index(fields=['pessoa']),
        ]

    def __str__(self):
        return f'{self.nome_visitante} — {self.chegou_em:%d/%m/%Y %H:%M}'

    @property
    def ainda_presente(self):
        """True se o visitante ainda não foi registrado como saído."""
        return self.saiu_em is None

    def registrar_saida(self):
        """Marca a saída agora."""
        from django.utils import timezone
        self.saiu_em = timezone.now()
        self.save(update_fields=['saiu_em', 'atualizado_em'])
