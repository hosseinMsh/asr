import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "channels",
    "asr",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "asr_gateway.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csrf",
            ],
        },
    },
]

WSGI_APPLICATION = "asr_gateway.wsgi.application"
ASGI_APPLICATION = "asr_gateway.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Asia/Tehran")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ASR_FASTAPI_URL = os.getenv("ASR_FASTAPI_URL", "http://127.0.0.1:8025/api/upload/")
ASR_FASTAPI_TIMEOUT = int(os.getenv("ASR_FASTAPI_TIMEOUT", "300"))

WORD_COST = float(os.getenv("WORD_COST", "0.05"))

DEFAULT_PLANS = {
    "anon": {
        "name": "Anonymous",
        "monthly_seconds_limit": int(os.getenv("ANON_MONTHLY_SECONDS", "120")),
        "max_file_size_mb": int(os.getenv("ANON_MAX_FILE_MB", "5")),
        "history_retention_days": int(os.getenv("ANON_HISTORY_DAYS", "1")),
    },
    "free": {
        "name": "Free",
        "monthly_seconds_limit": int(os.getenv("FREE_MONTHLY_SECONDS", "1800")),
        "max_file_size_mb": int(os.getenv("FREE_MAX_FILE_MB", "25")),
        "history_retention_days": int(os.getenv("FREE_HISTORY_DAYS", "7")),
    },
    "plus": {
        "name": "Plus",
        "monthly_seconds_limit": int(os.getenv("PLUS_MONTHLY_SECONDS", "14400")),
        "max_file_size_mb": int(os.getenv("PLUS_MAX_FILE_MB", "100")),
        "history_retention_days": int(os.getenv("PLUS_HISTORY_DAYS", "30")),
    },
    "pro": {
        "name": "Pro",
        "monthly_seconds_limit": int(os.getenv("PRO_MONTHLY_SECONDS", "43200")),
        "max_file_size_mb": int(os.getenv("PRO_MAX_FILE_MB", "250")),
        "history_retention_days": int(os.getenv("PRO_HISTORY_DAYS", "180")),
    },
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [os.getenv("CHANNEL_REDIS_URL", "redis://127.0.0.1:6379/2")]},
    }
}

REST_FRAMEWORK = {
'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("THROTTLE_ANON", "10/hour"),
        "user": os.getenv("THROTTLE_USER", "5000/day"),
    },
    "EXCEPTION_HANDLER": "asr.utils.errors.exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MIN", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Blog API',
    'DESCRIPTION': 'API for managing blog posts, comments, and categories',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}