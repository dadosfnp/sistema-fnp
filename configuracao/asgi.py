"""Configuração ASGI do Sistema FNP."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuracao.local')

application = get_asgi_application()
