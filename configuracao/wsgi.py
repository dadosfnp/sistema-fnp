"""Configuração WSGI do Sistema FNP."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuracao.local')

application = get_wsgi_application()
