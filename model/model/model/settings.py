from pathlib import Path
from os import environ

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = environ.get('SECRET_KEY', '16600cc09a28b8dd3b4b8e7cfb4e81ff7958a87ab81809386ba7dcff9d68547e')
DEBUG = True
ALLOWED_HOSTS = [environ.get('HOSTNAME', 'api.ai4mde.localhost'), 'localhost']

INSTALLED_APPS = [
    'model',
    'metadata',
    'diagram',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'model.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'model.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        'HOST': environ.get('POSTGRES_HOST', 'postgres'),
        'PORT': environ.get('POSTGRES_PORT', '5432'),
        'NAME': environ.get('POSTGRES_DB', 'ai4mdestudio'),
        'USER': environ.get('POSTGRES_USER', 'ai4mdestudio'),
        'PASSWORD': environ.get('POSTGRES_PASSWORD', 'ai4mdestudio'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
