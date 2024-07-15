from os import environ
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=environ.get("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        auto_session_tracking=False,
        traces_sample_rate=0
    )

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = environ.get(
    "SECRET_KEY", "16600cc09a28b8dd3b4b8e7cfb4e81ff7958a87ab81809386ba7dcff9d68547e"
)


# TODO: Find a more elegant solution for this
DEBUG = True
ALLOWED_HOSTS = ["*"]

if environ.get("DEBUG", "True").lower() == "false":
    DEBUG = False
    ALLOWED_HOSTS = [environ.get("HOSTNAME", "api.ai4mde.localhost"), "localhost"]

INSTALLED_APPS = [
    "daphne",  # ext: Use Daphne as ASGI server
    "model",  # The main app / project is the model application
    "metadata",  # The metadata app is used to store metadata such as projects, systems, users and so on
    "diagram",  # The diagram app is used to store diagram-specific data
    "prompt",  # The prompt app is used for the chat / prompting functionalities
    "prose",  # The prose app is used to store and build NLP pipelines
    "generator", # The generator app is used to store and build prototypes
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "drf_yasg",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "model.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "model.wsgi.application"
ASGI_APPLICATION = "model.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": environ.get(
            "POSTGRES_HOST", "postgres"
        ),  # Change this to localhost if can't use docker networking
        "PORT": environ.get("POSTGRES_PORT", "5432"),
        "NAME": environ.get("POSTGRES_DB", "ai4mdestudio"),
        "USER": environ.get("POSTGRES_USER", "ai4mdestudio"),
        "PASSWORD": environ.get("POSTGRES_PASSWORD", "ai4mdestudio"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # TODO: Investigate if need to change this to UUIDField
CSRF_TRUSTED_ORIGINS = [
    "http://localhost",  # TODO: Setup some environment variables for this
    "http://localhost:5173",
    "http://" + environ.get("HOSTNAME", "api.ai4mde.localhost"),
    "https://" + environ.get("HOSTNAME", "api.ai4mde.localhost"),
    "http://" + environ.get("STUDIO_HOSTNAME", "ai4mde.localhost"),
    "https://" + environ.get("STUDIO_HOSTNAME", "ai4mde.localhost"),

]
CSRF_COOKIE_DOMAIN = '.'.join(environ.get("HOSTNAME", "ai4mde.localhost").split('.')[1:])  # TODO: Test & investigate how to fix this stuff, so we can run from localhost:5173
CORS_ALLOW_ALL_ORIGINS = True  # TODO: Not in PROD!
CORS_ALLOW_CREDENTIALS = True  # TODO: Investigate if necessary?
CSRF_COOKIE_HTTPONLY = False  # TODO: Is this even used?

PROSE_API_KEY = (
    "sequoias"  # TODO: Leverage the JWT to make connections to the Prose API
)

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Basic': {
            'type': 'basic'
        }
    }
}