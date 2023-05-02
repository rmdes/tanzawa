"""
Django settings for web20core project.

Generated by 'django-admin startproject' using Django 3.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os
import secrets
from pathlib import Path

import django
from envparse import env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


env.read_envfile(path=os.environ.get("ENV_FILE"))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/


# SECURITY WARNING: keep the secret key used in production secret!
def get_secret_key() -> str:
    secret_key = env.str("SECRET_KEY", default="")
    if secret_key:
        return secret_key
    else:
        return secrets.token_urlsafe()


SECRET_KEY = get_secret_key()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)


def get_allowed_hosts() -> list[str]:
    """
    Get all hosts that are allowed to connect to Tanzawa.
    """
    allowed_hosts = env.list("ALLOWED_HOSTS", default=[])
    domain_name = env.str("DOMAIN_NAME", default="example.com")
    return allowed_hosts + [domain_name]


ALLOWED_HOSTS = get_allowed_hosts()

SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)

CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)


# Application definition

INSTALLED_APPS = [
    "interfaces.commands",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.gis",
    "rest_framework",
    "webmention",
    "meta",
    "core",
    "django_htmx",
    # Data layer
    "data",
    "data.entry",
    "data.settings",
    "data.streams",
    "data.trips",
    "data.post",
    "data.files",
    "data.indieweb",
    "data.wordpress",
    "data.plugins",
    "interfaces",
]

MIDDLEWARE = [
    "django.middleware.gzip.GZipMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "turbo_response.middleware.TurboMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "interfaces.common.middleware.settings.SettingsMiddleware",
    "webmention.middleware.webmention_middleware",
    "interfaces.common.middleware.plugins.PluginMiddleware",
]

ROOT_URLCONF = "core.urls"

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = [
        "127.0.0.1",
    ]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [Path(BASE_DIR) / "templates", django.__path__[0] + "/forms/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "libraries": {
                "indieweb": "interfaces.common.templatetags.indieweb",
                "plugins": "interfaces.common.templatetags.plugins",
            },
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.spatialite",
        "NAME": env.str("DB_NAME", default="db.sqlite3"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = env.str("LANGUAGE_CODE", default="en-us")

TIME_ZONE = env.str("TIME_ZONE", default="UTC")

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = "/static/"

THEMES_ROOT = BASE_DIR / "../front/src/themes"
THEMES = [path.stem for path in THEMES_ROOT.iterdir() if path.is_dir()]
THEME_STATICFILE_DIRS = [path for path in THEMES_ROOT.glob("**/static") if path.is_dir()]
STATICFILES_DIRS = [BASE_DIR / "../static/", *THEME_STATICFILE_DIRS]

STATIC_ROOT = Path(env.str("STATIC_ROOT", default="./staticfiles/"))
MEDIA_ROOT = Path(env.str("MEDIA_ROOT", default="./micropub_media/"))


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

SPATIALITE_LIBRARY_PATH = env.str("SPATIALITE_LIBRARY_PATH", default=None)

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "post:dashboard"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


# Homepage Settings
HIGHLIGHT_STREAM_SLUG: str | None = env.str("HIGHLIGHT_STREAM_SLUG", default=None)

PLUGINS = env.list("PLUGINS", default=[])

INSTALLED_APPS.extend(PLUGINS)

PLUGINS_RUN_MIGRATIONS_STARTUP = env.bool("PLUGINS_RUN_MIGRATIONS_STARTUP", default=True)

FORCE_ENABLED_PLUGINS = env.list("FORCE_ENABLED_PLUGINS", default=[])
# Open Graph Settings

META_SITE_DOMAIN = env.str("DOMAIN_NAME", default="example.com")
META_SITE_PROTOCOL = env.str("PROTOCOL", default="https")
META_USE_OG_PROPERTIES = env.bool("META_USE_OG_PROPERTIES", default=True)
META_USE_TWITTER_PROPERTIES = env.bool("META_USE_TWITTER_PROPERTIES", default=True)
META_USE_SCHEMAORG_PROPERTIES = env.bool("META_USE_SCHEMAORG_PROPERTIES", default=True)


# Exercise Plugin

STRAVA_CLIENT_ID = env.str("STRAVA_CLIENT_ID", default="")
STRAVA_CLIENT_SECRET = env.str("STRAVA_CLIENT_SECRET", default="")
