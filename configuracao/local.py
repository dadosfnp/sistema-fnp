"""
Configurações de desenvolvimento local.
"""

from pathlib import Path

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# CORS em dev: libera tudo (em prod usamos allowlist)
CORS_ALLOW_ALL_ORIGINS = True

# Banco de dados local — SQLite enquanto PostgreSQL não estiver disponível
# Quando instalar o PostgreSQL, remova este bloco para usar o DATABASES do base.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(__file__).resolve().parent.parent / 'db.sqlite3',
    }
}

# E-mail no console durante desenvolvimento
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
