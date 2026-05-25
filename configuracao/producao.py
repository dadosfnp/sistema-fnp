"""Configurações de produção (Render).

Lê variáveis sensíveis do ambiente. Usa dj-database-url para
interpretar a DATABASE_URL fornecida pelo Render e WhiteNoise
para servir arquivos estáticos coletados em STATIC_ROOT.
"""

import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401, F403

DEBUG = False

# ---------------------------------------------------------------------------
# Fail-fast em produção — variáveis sensíveis OBRIGATÓRIAS via ambiente.
# Subir o processo sem SECRET_KEY decente quebra criptografia de sessão, CSRF
# e tokens; melhor falhar no boot do que rodar com 'chave-insegura-...' no ar.
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY or 'insegura' in SECRET_KEY.lower() or len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        'SECRET_KEY ausente, fraca ou de desenvolvimento em produção. '
        'Defina a variável de ambiente SECRET_KEY com no mínimo 50 caracteres aleatórios. '
        'Gere com: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
    )

if not os.environ.get('DATABASE_URL'):
    raise ImproperlyConfigured(
        'DATABASE_URL ausente em produção. Configure a string de conexão PostgreSQL.'
    )

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

# Origens extras (ex: IP cru do droplet via http:// durante setup, domínio
# temporário em homologação). Lidas de EXTRA_CSRF_ORIGINS no .env como
# CSV de URLs completas:
#   EXTRA_CSRF_ORIGINS=http://203.0.113.45,https://homolog.fnp.org.br
# Útil enquanto o certbot ainda não emitiu o certificado e o acesso é
# feito via IP — sem isso, o Django bloqueia o POST de login com 403 CSRF.
EXTRA_CSRF_ORIGINS = [
    origem.strip()
    for origem in os.environ.get('EXTRA_CSRF_ORIGINS', '').split(',')
    if origem.strip()
]
CSRF_TRUSTED_ORIGINS.extend(EXTRA_CSRF_ORIGINS)

# CORS — em produção libera só os hosts do próprio sistema (face-api.js
# acessando /media/ e clientes da API REST que rodam no mesmo domínio).
CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS[:]

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
        # CompressedStaticFilesStorage (sem 'Manifest') é a versão tolerante:
        # comprime e serve gzipped, mas não exige que TODOS os {% static %}
        # apontem para arquivos existentes. O manifest estrito quebrava o
        # collectstatic em produção quando havia referências legadas (favicons,
        # SVGs antigos) que somem em refactors. Em troca não temos hash no
        # nome — cache busting depende do header Cache-Control do WhiteNoise.
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
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
