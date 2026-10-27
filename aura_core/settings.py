"""
AURA STAGE // LUMINA STUDIO — Django Settings
Production-grade configuration for the AI Event Planner & Spatial Furniture Budget Planner.

STRICT ZERO-INSTALL RULE: no third-party packages beyond Django 6.1.2 built-ins.
Room uploads use models.FileField (no Pillow dependency).
"""

import os
from pathlib import Path

# ------------------------------------------------------------------ #
#  Paths                                                              #
# ------------------------------------------------------------------ #
BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Tiny stdlib .env loader (zero-install rule — no python-dotenv).

    Loads KEY="value" / KEY=value lines into os.environ without
    overwriting variables that are already set in the real environment.
    Values are never printed or logged anywhere in this project.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_dotenv(BASE_DIR / ".env")

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
# Optional server-side vision keys, read from the environment / .env.
# Precedence at runtime: user-pasted browser key > GROQ > GEMINI > none.
# If nothing is available the local Knapsack Budget Optimizer runs 100% offline.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)
GEMINI_TIMEOUT_SECONDS = 25

# Groq — OpenAI-compatible Vision API (ultra-fast Llama vision models).
# The .env in this project ships GROQ_API_KEY; it is auto-loaded above by
# _load_dotenv(), so no extra packages and no hard-coded secret in source.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get(
    "GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
)  # vision-capable; override via .env if your org access differs
GROQ_FALLBACK_MODELS = [
    "meta-llama/llama-4-sonar-70b-8b-instruct",  # vision fallback
]
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TIMEOUT_SECONDS = 30

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
