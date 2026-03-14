from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BASE_DIR.parent


def env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def env_required(key: str) -> str:
    value = os.environ.get(key)
    if value is not None and value.strip():
        return value
    raise RuntimeError(f"Environment variable '{key}' is required for this settings module.")


def env_optional(key: str) -> str | None:
    value = os.environ.get(key)
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def env_list(key: str, default: str) -> list[str]:
    value = os.environ.get(key, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _sanitize_identifier_component(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_")


def build_test_database_name(
    database_name: str,
    *,
    explicit_name: str | None = None,
    explicit_suffix: str | None = None,
    generated_suffix: str | None = None,
) -> str:
    if explicit_name is not None:
        return explicit_name

    suffix = explicit_suffix or generated_suffix
    if suffix is None:
        raise ValueError(
            "A test database suffix is required when no explicit test database name is set."
        )

    normalized_suffix = _sanitize_identifier_component(suffix)[:24] or "session"
    candidate_prefix = f"test_{database_name}"
    max_prefix_length = 63 - len(normalized_suffix) - 1
    normalized_prefix = candidate_prefix[:max_prefix_length].rstrip("_") or "test"
    return f"{normalized_prefix}_{normalized_suffix}"


def default_test_database_suffix() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    return f"{timestamp}_{os.getpid()}"


CURRENT_SETTINGS_MODULE = env("DJANGO_SETTINGS_MODULE", "config.settings.dev")
IS_DEV_SETTINGS = CURRENT_SETTINGS_MODULE == "config.settings.dev"

DEFAULT_DATABASE_NAME = (
    env("POSTGRES_DB", "dle_saas") if IS_DEV_SETTINGS else env_required("POSTGRES_DB")
)
DEFAULT_DATABASE_USER = (
    env("POSTGRES_USER", "dle_saas") if IS_DEV_SETTINGS else env_required("POSTGRES_USER")
)
DEFAULT_DATABASE_PASSWORD = (
    env("POSTGRES_PASSWORD", "dle_saas") if IS_DEV_SETTINGS else env_required("POSTGRES_PASSWORD")
)

if IS_DEV_SETTINGS:
    SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-dle-saas-local-dev-key")
else:
    SECRET_KEY = env_required("DJANGO_SECRET_KEY")

DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.audit.apps.AuditConfig",
    "apps.sites.apps.SitesConfig",
    "apps.authz.apps.AuthzConfig",
    "apps.mmr.apps.MmrConfig",
    "apps.batches.apps.BatchesConfig",
    "apps.exports.apps.ExportsConfig",
    "apps.reviews.apps.ReviewsConfig",
    "rest_framework",
    "drf_spectacular",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
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
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DEFAULT_DATABASE_NAME,
        "USER": DEFAULT_DATABASE_USER,
        "PASSWORD": DEFAULT_DATABASE_PASSWORD,
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(env("POSTGRES_CONN_MAX_AGE", "60")),
    }
}
DATABASES["default"]["TEST"] = {
    "NAME": build_test_database_name(
        DEFAULT_DATABASE_NAME,
        explicit_name=env_optional("POSTGRES_TEST_DB_NAME"),
        explicit_suffix=env_optional("POSTGRES_TEST_DB_SUFFIX"),
        generated_suffix=default_test_database_suffix(),
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", "Europe/Paris")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "authz.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "workstation_identify": "10/minute",
        "workstation_lock": "10/minute",
        "signature_reauth": "10/minute",
    },
    "EXCEPTION_HANDLER": "shared.api.exceptions.problem_details_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "DLE-SaaS API",
    "DESCRIPTION": "Canonical OpenAPI contract for the DLE-SaaS backend foundation.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
