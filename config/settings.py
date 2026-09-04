"""
Django settings for the Document QA RAG project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# Helpers

def env_bool(
    name,
    default=False,
):
    return os.getenv(
        name,
        str(default),
    ).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


# Security

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-development-only-key",
)

DEBUG = env_bool(
    "DJANGO_DEBUG",
    True,
)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1",
    ).split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]

SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    False,
)

SESSION_COOKIE_SECURE = env_bool(
    "DJANGO_SESSION_COOKIE_SECURE",
    False,
)

CSRF_COOKIE_SECURE = env_bool(
    "DJANGO_CSRF_COOKIE_SECURE",
    False,
)

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# Application definition

INSTALLED_APPS = [
    # Local applications
    "apps.documents.apps.DocumentsConfig",
    "apps.qa.apps.QAConfig",

    # Third-party applications
    "rest_framework",
    "drf_spectacular",
    "drf_spectacular_sidecar",

    # Django applications
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django.DjangoTemplates"
        ),
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv(
            "DB_NAME",
            "document_qa",
        ),
        "USER": os.getenv(
            "DB_USER",
            "document_qa_user",
        ),
        "PASSWORD": os.getenv(
            "DB_PASSWORD",
            "",
        ),
        "HOST": os.getenv(
            "DB_HOST",
            "127.0.0.1",
        ),
        "PORT": os.getenv(
            "DB_PORT",
            "5433",
        ),
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files

STATIC_URL = "/static/"

STATIC_ROOT = Path(
    os.getenv(
        "STATIC_ROOT",
        BASE_DIR / "staticfiles",
    )
)

STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedStaticFilesStorage"
        ),
    },
}


# Uploaded media files

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_SCHEMA_CLASS": (
        "drf_spectacular.openapi.AutoSchema"
    ),
    "EXCEPTION_HANDLER": (
        "config.api_exceptions.api_exception_handler"
    ),
}


# OpenAPI documentation

SPECTACULAR_SETTINGS = {
    "TITLE": "Document QA RAG API",
    "DESCRIPTION": (
        "REST API for DOCX document management, semantic retrieval, "
        "and document-grounded question answering."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayOperationId": True,
    },
}


# Embeddings

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

EMBEDDING_DEVICE = os.getenv(
    "EMBEDDING_DEVICE",
    "cpu",
)

EMBEDDING_BATCH_SIZE = int(
    os.getenv(
        "EMBEDDING_BATCH_SIZE",
        "32",
    )
)

EMBEDDING_DIMENSION = 384


# OpenRouter

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    "",
)

OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "thinkingmachines/inkling:free",
)

OPENROUTER_FALLBACK_MODELS = [
    model.strip()
    for model in os.getenv(
        "OPENROUTER_FALLBACK_MODELS",
        (
            "thinkingmachines/inkling-small:free,"
            "liquid/lfm-2.5-2.6b:free"
        ),
    ).split(",")
    if model.strip()
]

OPENROUTER_APP_URL = os.getenv(
    "OPENROUTER_APP_URL",
    "http://localhost:8000",
)

OPENROUTER_APP_NAME = os.getenv(
    "OPENROUTER_APP_NAME",
    "Document QA RAG",
)

OPENROUTER_TEMPERATURE = float(
    os.getenv(
        "OPENROUTER_TEMPERATURE",
        "0",
    )
)

OPENROUTER_MAX_TOKENS = int(
    os.getenv(
        "OPENROUTER_MAX_TOKENS",
        "512",
    )
)

OPENROUTER_TIMEOUT_MS = int(
    os.getenv(
        "OPENROUTER_TIMEOUT_MS",
        "120000",
    )
)

OPENROUTER_MAX_RETRIES = int(
    os.getenv(
        "OPENROUTER_MAX_RETRIES",
        "1",
    )
)


# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"