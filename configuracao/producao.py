"""Configurações de produção (Render).

Lê variáveis sensíveis do ambiente. Usa dj-database-url para
interpretar a DATABASE_URL fornecida pelo Render e WhiteNoise
para servir arquivos estáticos coletados em STATIC_ROOT.
"""

import os

import dj_database_url

from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', '.onrender.com').split(',')
    if host.strip()
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    f"https://{host.lstrip('.')}" if host.startswith('.') else f"https://{host}"
    for host in ALLOWED_HOSTS
]

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', ''),
        conn_max_age=600,
        ssl_require=True,
    )
}

MIDDLEWARE.insert(
    1,
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8h — alinhado a dia útil
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 dias — escalar pra 1 ano depois de validar
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
X_FRAME_OPTIONS = 'DENY'

# Tamanho máximo de upload de arquivo (10 MB padrão; ajustar conforme necessidade)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Logging básico de produção — captura warnings/erros do Django no stdout do Render.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simples': {'format': '[{asctime}] {levelname} {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simples'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django.request': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'django.security': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
