"""Models de Eventos — acontecimentos pontuais com participação pontuada.

Campos refletem a aba "Eventos" da máscara FNP: tipo (assembléia, congresso,
seminário etc.), acesso (público/privado), objetivo, natureza (deliberativo
/consultivo/formativo) e vínculo opcional a uma Instância (Espaço de Diálogo
Federativo). Participações geram pontos para o município vinculado.
"""

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.instancias.models import Instancia
from aplicacoes.nucleo.models import ModeloBase


class Evento(ModeloBase):
    """Evento institucional da FNP com configuração de pontos por modalidade e papel.

    Cada evento tem tipo (categoria conceitual), acesso (regra de entrada),
    objetivo institucional, natureza decisória e modalidade (presencial/virtual).
    Pontuação base é configurável por evento e somada com bônus de palestrante/
    organizador na Participação.
    """

    class TipoEvento(models.TextChoices):
        ASSEMBLEIA_GERAL = 'assembleia_geral', 'Assembléia Geral'
        AUDIENCIA = 'audiencia', 'Audiência'
        COMISSOES = 'comissoes', 'Comissões'
        CONFERENCIA = 'conferencia', 'Conferência'
        CONGRESSO = 'congresso', 'Congresso'
        GRUPOS_TRABALHO = 'grupos_trabalho', 'Grupos de Trabalho'
        MISSAO_INTERNACIONAL = 'missao_internacional', 'Missão Internacional'
        REUNIAO_PROJETO = 'reuniao_projeto', 'Reunião de Projeto'
        SEMINARIO = 'seminario', 'Seminário'
        WORKSHOP = 'workshop', 'Workshop'
        REUNIAO_GERAL = 'reuniao_geral', 'Reunião Geral da FNP'
        FORUM = 'forum', 'Fórum'
        VIAGEM_INTERNACIONAL = 'viagem_internacional', 'Viagem internacional'
        VIAGEM_NACIONAL = 'viagem_nacional', 'Viagem nacional'
        REUNIAO_PRESENCIAL = 'reuniao_presencial', 'Reunião presencial na FNP'
        REUNIAO_ONLINE = 'reuniao_online', 'Reunião online'
        WEBINAR = 'webinar', 'Webinar'
        PRESENCA_FNP = 'presenca_fnp', 'Presença na FNP'

    class AcessoEvento(models.TextChoices):
        PUBLICO = 'publico', 'Público'
        PRIVADO = 'privado', 'Privado'
        RESTRITO = 'restrito', 'Restrito'
        GRATUITO = 'gratuito', 'Gratuito'
        INSCRICAO_PAGA = 'inscricao_paga', 'Inscrição paga'

    class TipoParticipacaoFNP(models.TextChoices):
        APOIO_INSTITUCIONAL = 'apoio_institucional', 'Apoio Institucional'
        REALIZACAO = 'realizacao', 'Realização'
        CO_REALIZACAO = 'co_realizacao', 'Co-realização'
        PATROCINADOR = 'patrocinador', 'Patrocinador'
        TECNICO = 'tecnico', 'Técnico'
        POLITICO_INSTITUCIONAL = 'politico_institucional', 'Político-institucional'

    class ObjetivoEvento(models.TextChoices):
        ARTICULACAO_POLITICA = 'articulacao_politica', 'Articulação política'
        FORMACAO = 'formacao', 'Formação / Capacitação'
        INCIDENCIA_INSTITUCIONAL = 'incidencia_institucional', 'Incidência institucional'
        TOMADA_DECISAO = 'tomada_decisao', 'Tomada de decisão'

    class NaturezaEvento(models.TextChoices):
        DELIBERATIVO = 'deliberativo', 'Deliberativo'
        CONSULTIVO = 'consultivo', 'Consultivo'
        FORMATIVO = 'formativo', 'Formativo'

    class Modalidade(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        ONLINE = 'online', 'Online'
        HIBRIDO = 'hibrido', 'Híbrido'

    titulo = models.CharField('título', max_length=255)
    tipo = models.CharField(
        'tipo',
        max_length=25,
        choices=TipoEvento.choices,
    )
    acesso = models.CharField(
        'acesso ao evento',
        max_length=20,
        choices=AcessoEvento.choices,
        default=AcessoEvento.PUBLICO,
    )
    tipo_participacao_fnp = models.CharField(
        'tipo de participação da FNP',
        max_length=25,
        choices=TipoParticipacaoFNP.choices,
        blank=True,
        help_text='Papel da FNP no evento (apoio, realização, patrocínio etc.).',
    )
    objetivo = models.CharField(
        'objetivo',
        max_length=30,
        choices=ObjetivoEvento.choices,
        blank=True,
    )
    natureza = models.CharField(
        'natureza',
        max_length=15,
        choices=NaturezaEvento.choices,
        blank=True,
    )
    modalidade = models.CharField(
        'modalidade',
        max_length=15,
        choices=Modalidade.choices,
        default=Modalidade.PRESENCIAL,
    )
    instancia_vinculada = models.ForeignKey(
        Instancia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_vinculados',
        verbose_name='instância vinculada',
        help_text='Espaço de Diálogo Federativo ao qual o evento está relacionado, se houver.',
    )
    data_inicio = models.DateField('data de início')
    data_fim = models.DateField('data de término', blank=True, null=True)
    local = models.CharField('local (lugar)', max_length=255, blank=True)
    cidade = models.CharField('cidade', max_length=150, blank=True)
    uf = models.CharField('UF', max_length=2, blank=True, choices=Municipio.UF_CHOICES)
    descricao = models.TextField('descrição', blank=True)
    pontos_presencial = models.IntegerField(
        'pontos (presencial)',
        default=10,
        help_text='Pontos para participação presencial.',
    )
    pontos_online = models.IntegerField(
        'pontos (online)',
        default=5,
        help_text='Pontos para participação online. 0 se não aplicável.',
    )
    pontos_palestrante_bonus = models.IntegerField(
        'bônus palestrante',
        default=5,
        help_text='Pontos extras para quem palestrou.',
    )
    pontos_organizador_bonus = models.IntegerField(
        'bônus organizador',
        default=5,
        help_text='Pontos extras para quem organizou.',
    )
    documentos = GenericRelation(
        'documentos.Documento',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='evento',
    )
    presencas = GenericRelation(
        'presenca.Presenca',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='evento',
    )

    class Meta:
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'
        ordering = ['-data_inicio']
        indexes = [
            models.Index(fields=['-data_inicio']),
            models.Index(fields=['tipo']),
            models.Index(fields=['modalidade']),
        ]

    def __str__(self):
        return f'{self.titulo} ({self.get_tipo_display()})'


class Participacao(ModeloBase):
    """Participação de uma pessoa em um evento — gera pontos para o município vinculado."""

    class FormaParticipacao(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        ONLINE = 'online', 'Online'

    class PapelNoEvento(models.TextChoices):
        PARTICIPANTE = 'participante', 'Participante'
        PALESTRANTE = 'palestrante', 'Palestrante'
        ORGANIZADOR = 'organizador', 'Organizador(a)'
        MODERADOR = 'moderador', 'Moderador(a)'
        COORDENACAO = 'coordenacao', 'Coordenação'
        EXPOSITOR = 'expositor', 'Expositor'
        OBSERVADOR = 'observador', 'Observador'

    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name='participacoes',
        verbose_name='pessoa',
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='participacoes',
        verbose_name='evento',
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.CASCADE,
        related_name='participacoes',
        verbose_name='município que recebe os pontos',
        help_text='Município que será pontuado por esta participação.',
    )
    forma_participacao = models.CharField(
        'forma de participação',
        max_length=15,
        choices=FormaParticipacao.choices,
        default=FormaParticipacao.PRESENCIAL,
    )
    papel_no_evento = models.CharField(
        'papel no evento',
        max_length=15,
        choices=PapelNoEvento.choices,
        default=PapelNoEvento.PARTICIPANTE,
    )
    confirmado = models.BooleanField('confirmado?', default=False)
    pontos_calculados = models.IntegerField(
        'pontos calculados',
        default=0,
        help_text='Pontos atribuídos automaticamente ao salvar.',
    )
    data_confirmacao = models.DateTimeField('data de confirmação', blank=True, null=True)

    class Meta:
        verbose_name = 'participação'
        verbose_name_plural = 'participações'
        ordering = ['-criado_em']
        unique_together = ['pessoa', 'evento']
        indexes = [
            models.Index(fields=['confirmado']),
            models.Index(fields=['municipio', 'confirmado']),
            models.Index(fields=['evento', 'confirmado']),
        ]

    def __str__(self):
        return f'{self.pessoa} em {self.evento}'

    def calcular_pontos(self):
        """Calcula pontos com base na forma de participação e papel no evento.

        Returns:
            int: Pontos base (presencial/online) + bônus por papel (palestrante/organizador).
        """
        evento = self.evento
        if self.forma_participacao == self.FormaParticipacao.PRESENCIAL:
            pontos = evento.pontos_presencial
        else:
            pontos = evento.pontos_online

        if self.papel_no_evento == self.PapelNoEvento.PALESTRANTE:
            pontos += evento.pontos_palestrante_bonus
        elif self.papel_no_evento == self.PapelNoEvento.ORGANIZADOR:
            pontos += evento.pontos_organizador_bonus

        return pontos

    def save(self, *args, **kwargs):
        """Recalcula pontos automaticamente antes de persistir."""
        self.pontos_calculados = self.calcular_pontos()
        super().save(*args, **kwargs)
