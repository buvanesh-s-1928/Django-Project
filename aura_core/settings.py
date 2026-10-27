"""
AURA STAGE // LUMINA STUDIO — Django Settings
Production-grade configuration for the AI Event Planner & Spatial Furniture Budget Planner.

STRICT ZERO-INSTALL RULE: no third-party packages beyond Django 6.1.2 built-ins.
Room uploads use models.FileField (no Pillow dependency).
"""

from pathlib import Path

# ------------------------------------------------------------------ #
#  Paths                                                              #
# ------------------------------------------------------------------ #
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------ #
#  Security                                                           #
# ------------------------------------------------------------------ #
SECRET_KEY = "django-insecure-aura-stage-lumina-0x7f3c9b2e-dev-only-key"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# ------------------------------------------------------------------ #
#  Applications                                                       #
# ------------------------------------------------------------------ #
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # ── AURA Core ──────────────────────────────────────────────
    "studio",
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

ROOT_URLCONF = "aura_core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "studio.context_processors.aura_context",
            ],
        },
    },
]

WSGI_APPLICATION = "aura_core.wsgi.application"
ASGI_APPLICATION = "aura_core.asgi.application"

# ------------------------------------------------------------------ #
#  Database — SQLite (zero-config, offline-first)                     #
# ------------------------------------------------------------------ #
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------ #
#  Password validation                                                #
# ------------------------------------------------------------------ #
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------ #
#  Internationalisation                                               #
# ------------------------------------------------------------------ #
LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------ #
#  Static & Media                                                     #
# ------------------------------------------------------------------ #
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "studio" / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Room photos arrive via FileField — cap at 12 MB to stay sane.
FILE_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024

# ------------------------------------------------------------------ #
#  Session / CSRF                                                     #
# ------------------------------------------------------------------ #
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # one week
CSRF_COOKIE_HTTPONLY = False           # JS reads csrftoken for the API POST

# ------------------------------------------------------------------ #
#  AURA Engine flags                                                  #
# ------------------------------------------------------------------ #
# Optional server-side Gemini key. If absent, users may paste their own
# key in the telemetry-bar modal; if neither exists the local
# Knapsack Budget Optimizer runs 100% offline.
GEMINI_API_KEY = ""  # e.g. os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)
GEMINI_TIMEOUT_SECONDS = 25

# Currency formatting used across templates + API payloads.
CURRENCY_SYMBOL = "₹"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "studio": {"handlers": ["console"], "level": "INFO"},
    },
}
