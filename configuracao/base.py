"""
Configurações base do Django para o Sistema FNP.
Configurações compartilhadas entre todos os ambientes.
"""

import os
from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-insegura-troque-em-producao')

DEBUG = False

ALLOWED_HOSTS = []

# ---------------------------------------------------------------------------
# Apps
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',  # deve vir após unfold
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
]

# DRF — autenticação por token + session, somente leitura para clientes externos
# por enquanto. Pagina respostas grandes automaticamente.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/hour',
        'anon': '20/hour',
    },
}

LOCAL_APPS = [
    'aplicacoes.nucleo',
    'aplicacoes.cadastro',
    'aplicacoes.instancias',
    'aplicacoes.projetos',
    'aplicacoes.missoes',
    'aplicacoes.atividades',
    'aplicacoes.eventos',
    'aplicacoes.documentos',
    'aplicacoes.dicionario',
    'aplicacoes.presenca',
    'aplicacoes.comunicacao',
    'aplicacoes.adimplencia',
    'aplicacoes.engajamento',
    'aplicacoes.relatorios',
]

INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # CORS antes de tudo, para liberar /media/ e /api/ ao face-api.js e clientes externos
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'aplicacoes.nucleo.middleware.IsolarPortalPrefeitoMiddleware',
]

# CORS — libera /media/ (fotos) e /api/v1/ (REST) para origens same-origin
# por padrão. Em produção, ajustar CORS_ALLOWED_ORIGINS se for consumir de outro domínio.
CORS_URLS_REGEX = r'^/(media|api)/.*$'
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS: list = []  # populado em local.py e producao.py
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'configuracao.urls'

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'aplicacoes.nucleo.context_processors.perfil_usuario',
            ],
        },
    },
]

WSGI_APPLICATION = 'configuracao.wsgi.application'

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'sistema_fnp'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# ---------------------------------------------------------------------------
# Validação de senha
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internacionalização
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Arquivos estáticos
# ---------------------------------------------------------------------------
STATIC_URL = 'estaticos/'
STATICFILES_DIRS = [BASE_DIR / 'estaticos']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------------------
# Campo auto padrão
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/entrar/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/entrar/'

# Remetente padrão da mala direta. Pode ser sobrescrito por env var em produção.
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'sistema@fnp.org.br')

# ---------------------------------------------------------------------------
# Django Unfold — configuração do admin
# ---------------------------------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "Sistema FNP",
    "SITE_HEADER": "Sistema FNP",
    "SITE_SYMBOL": "groups",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Controle",
                "separator": True,
                "items": [
                    {
                        "title": "Pessoas",
                        "icon": "person",
                        "link": reverse_lazy("admin:cadastro_pessoa_changelist"),
                    },
                    {
                        "title": "Municípios",
                        "icon": "location_city",
                        "link": reverse_lazy("admin:cadastro_municipio_changelist"),
                    },
                    {
                        "title": "Vínculos",
                        "icon": "link",
                        "link": reverse_lazy("admin:cadastro_vinculomunicipio_changelist"),
                    },
                ],
            },
            {
                "title": "Categorias",
                "separator": True,
                "items": [
                    {
                        "title": "Espaços de Diálogo Federativo",
                        "icon": "forum",
                        "link": reverse_lazy("admin:instancias_instancia_changelist"),
                    },
                    {
                        "title": "Projetos",
                        "icon": "assignment",
                        "link": reverse_lazy("admin:projetos_projeto_changelist"),
                    },
                    {
                        "title": "Missões",
                        "icon": "flight_takeoff",
                        "link": reverse_lazy("admin:missoes_missao_changelist"),
                    },
                    {
                        "title": "Atividades",
                        "icon": "event_note",
                        "link": reverse_lazy("admin:atividades_atividade_changelist"),
                    },
                    {
                        "title": "Eventos",
                        "icon": "event",
                        "link": reverse_lazy("admin:eventos_evento_changelist"),
                    },
                ],
            },
            {
                "title": "Gestão",
                "separator": True,
                "items": [
                    {
                        "title": "Adimplência",
                        "icon": "payments",
                        "link": reverse_lazy("admin:adimplencia_adimplencia_changelist"),
                    },
                    {
                        "title": "Engajamento",
                        "icon": "trending_up",
                        "link": reverse_lazy("admin:engajamento_engajamento_changelist"),
                    },
                ],
            },
            {
                "title": "Participações e Representações",
                "separator": True,
                "items": [
                    {
                        "title": "Representações em Instâncias",
                        "icon": "groups",
                        "link": reverse_lazy("admin:instancias_representacao_changelist"),
                    },
                    {
                        "title": "Participações em Eventos",
                        "icon": "how_to_reg",
                        "link": reverse_lazy("admin:eventos_participacao_changelist"),
                    },
                    {
                        "title": "Delegações de Missões",
                        "icon": "group",
                        "link": reverse_lazy("admin:missoes_membrodelegacao_changelist"),
                    },
                    {
                        "title": "Presenças (universal)",
                        "icon": "fact_check",
                        "link": reverse_lazy("admin:presenca_presenca_changelist"),
                    },
                ],
            },
            {
                "title": "Comunicação",
                "separator": True,
                "items": [
                    {
                        "title": "Templates de e-mail",
                        "icon": "mail",
                        "link": reverse_lazy("admin:comunicacao_templateemail_changelist"),
                    },
                    {
                        "title": "Envios realizados",
                        "icon": "outgoing_mail",
                        "link": reverse_lazy("admin:comunicacao_envio_changelist"),
                    },
                ],
            },
            {
                "title": "Ajuda",
                "separator": True,
                "items": [
                    {
                        "title": "Dicionário",
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:dicionario_termodicionario_changelist"),
                    },
                    {
                        "title": "Pesos do Engajamento",
                        "icon": "scale",
                        "link": reverse_lazy("admin:engajamento_pesoengajamento_changelist"),
                    },
                ],
            },
        ],
    },
}
