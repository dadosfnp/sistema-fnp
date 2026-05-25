"""Configura o SocialApp Google OAuth lendo das variaveis de ambiente.

Idempotente: pode rodar quantas vezes precisar. Lê GOOGLE_OAUTH_CLIENT_ID
e GOOGLE_OAUTH_CLIENT_SECRET do .env e popula a tabela do allauth.

Uso:
    python manage.py configurar_google_oauth
"""

import os

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Cria/atualiza o SocialApp Google OAuth com base no .env.'

    def handle(self, *args, **opts):
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '').strip()
        client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '').strip()

        if not client_id or not client_secret:
            raise CommandError(
                'GOOGLE_OAUTH_CLIENT_ID e GOOGLE_OAUTH_CLIENT_SECRET devem estar no .env. '
                'Veja .env.exemplo para o passo a passo.'
            )

        from allauth.socialaccount.models import SocialApp

        site = Site.objects.first()
        if not site:
            raise CommandError('Nenhum Site cadastrado. Rode `manage.py migrate` primeiro.')

        app, criado = SocialApp.objects.update_or_create(
            provider='google', name='Google OAuth (FNP)',
            defaults={
                'client_id': client_id,
                'secret': client_secret,
                'key': '',
            },
        )
        app.sites.add(site)

        verbo = 'criado' if criado else 'atualizado'
        self.stdout.write(self.style.SUCCESS(
            f'SocialApp Google OAuth {verbo} com sucesso. Site: {site.domain}'
        ))
