"""Seed de templates de e-mail por categoria — exemplos institucionais da FNP."""

from django.core.management.base import BaseCommand

from aplicacoes.comunicacao.models import TemplateEmail


TEMPLATES = [
    (
        'Convite para reuniao da instancia', 'instancias',
        'Convocacao: {{ entidade }}',
        'Prezado(a) {{ pessoa }},\n\n'
        'Convidamos voce para a proxima reuniao da {{ entidade }}, na qual '
        'representa {{ municipio }}.\n\n'
        'A pauta e a programacao sao detalhadas no portal da FNP.\n\n'
        'Atenciosamente,\nFrente Nacional de Prefeitos',
    ),
    (
        'Atualizacao de projeto', 'projetos',
        'Atualizacao do projeto: {{ entidade }}',
        'Ola {{ pessoa }},\n\n'
        'Compartilhamos uma atualizacao do projeto {{ entidade }}, no qual '
        'voce esta envolvido(a) pelo municipio de {{ municipio }}.\n\n'
        'Detalhes completos no portal da FNP.\n\n'
        'Equipe FNP',
    ),
    (
        'Briefing de missao', 'missoes',
        'Briefing da missao: {{ entidade }}',
        'Prezado(a) {{ pessoa }},\n\n'
        'Segue o briefing inicial da missao {{ entidade }}. Sua participacao '
        'foi confirmada e os detalhes logisticos serao enviados em seguida.\n\n'
        'Equipe FNP',
    ),
    (
        'Lembrete de atividade', 'atividades',
        'Lembrete: reuniao da {{ entidade }}',
        'Ola {{ pessoa }},\n\n'
        'Este e um lembrete da proxima reuniao da {{ entidade }}. Contamos '
        'com sua presenca como representante de {{ municipio }}.\n\n'
        'Equipe FNP',
    ),
    (
        'Confirmacao de participacao em evento', 'eventos',
        'Sua participacao em: {{ entidade }}',
        'Prezado(a) {{ pessoa }},\n\n'
        'Sua participacao no evento {{ entidade }} foi registrada. Em breve '
        'voce recebera mais informacoes operacionais.\n\n'
        'Equipe FNP',
    ),
    (
        'Comunicado geral', 'geral',
        'Comunicado FNP',
        'Prezado(a) {{ pessoa }},\n\n'
        'Comunicado institucional sobre {{ entidade }}.\n\n'
        'Frente Nacional de Prefeitos',
    ),
]


class Command(BaseCommand):
    """Cria/atualiza templates de e-mail padrao por categoria."""

    help = 'Popula a tabela TemplateEmail com modelos institucionais por categoria.'

    def handle(self, *args, **options):
        criados = 0
        atualizados = 0
        for nome, categoria, assunto, corpo in TEMPLATES:
            _, criado = TemplateEmail.objects.update_or_create(
                nome=nome,
                defaults={
                    'categoria': categoria,
                    'assunto': assunto,
                    'corpo': corpo,
                    'ativo': True,
                },
            )
            if criado:
                criados += 1
            else:
                atualizados += 1
        self.stdout.write(self.style.SUCCESS(
            f'Concluido: {criados} criados, {atualizados} atualizados.'
        ))
