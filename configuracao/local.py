"""
Configurações de desenvolvimento local.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# E-mail no console durante desenvolvimento
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
