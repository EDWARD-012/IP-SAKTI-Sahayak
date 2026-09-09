"""
IP-SAKTI Sahayak — Django Settings
=====================================
Environment-driven configuration via python-dotenv + os.environ.
All secrets MUST come from the .env file — never hardcode.

Usage:
    Development:   python manage.py runserver
    Production:    set DJANGO_SETTINGS_MODULE=ip_sakti.settings + DEMO_MODE=False
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)

# ── Core secrets ───────────────────────────────────────────────
SECRET_KEY: str = os.environ.get(
    "SECRET_KEY",
    "django-insecure-CHANGE-THIS-IN-PRODUCTION-minimum-50-chars!!"
)
DEBUG: bool = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS: list[str] = [
    h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]
# Railway / PaaS public hostnames
for _host_key in ("RAILWAY_PUBLIC_DOMAIN", "RAILWAY_STATIC_URL", "RENDER_EXTERNAL_HOSTNAME"):
    _h = os.environ.get(_host_key, "").strip().removeprefix("https://").removeprefix("http://").split("/")[0]
    if _h and _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)
if os.environ.get("RAILWAY_ENVIRONMENT") and ".up.railway.app" not in ",".join(ALLOWED_HOSTS):
    ALLOWED_HOSTS.append(".up.railway.app")

_csrf_origins = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
for _h in ALLOWED_HOSTS:
    if _h and not _h.startswith(".") and _h not in ("localhost", "127.0.0.1", "0.0.0.0", "*"):
        for _scheme in ("https", "http"):
            _origin = f"{_scheme}://{_h}"
            if _origin not in _csrf_origins:
                _csrf_origins.append(_origin)
CSRF_TRUSTED_ORIGINS: list[str] = _csrf_origins

# ── Application definition ─────────────────────────────────────
INSTALLED_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "django_htmx",
    # Local apps
    "core.apps.CoreConfig",
    "chat.apps.ChatConfig",
    "corpus.apps.CorpusConfig",
    "wizard.apps.WizardConfig",
]

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",       # static files in production
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",        # i18n language from session/Accept-Language
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",            # adds request.htmx
    "csp.middleware.CSPMiddleware",                     # Content-Security-Policy
]

ROOT_URLCONF: str = "ip_sakti.urls"

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
                "django.template.context_processors.i18n",
                "core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION: str = "ip_sakti.wsgi.application"
ASGI_APPLICATION: str = "ip_sakti.asgi.application"

# ── Database ───────────────────────────────────────────────────
# Local default: SQLite (DATA_DIR / db.sqlite3).
# Cloud: set DATABASE_URL=postgresql://... (Railway Postgres service).
_DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR))).resolve()
try:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

_DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if _DATABASE_URL.startswith(("postgres://", "postgresql://")):
    import urllib.parse as _urlparse

    # django-postgres expects postgresql://
    if _DATABASE_URL.startswith("postgres://"):
        _DATABASE_URL = "postgresql://" + _DATABASE_URL[len("postgres://"):]
    _u = _urlparse.urlparse(_DATABASE_URL)
    _q = dict(_urlparse.parse_qsl(_u.query))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": (_u.path or "/railway").lstrip("/") or "railway",
            "USER": _urlparse.unquote(_u.username or ""),
            "PASSWORD": _urlparse.unquote(_u.password or ""),
            "HOST": _u.hostname or "",
            "PORT": str(_u.port or 5432),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
            "OPTIONS": {
                **({"sslmode": _q["sslmode"]} if _q.get("sslmode") else {}),
            },
        }
    }
else:
    _sqlite_name = os.environ.get("SQLITE_PATH", str(_DATA_DIR / "db.sqlite3"))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _sqlite_name,
            "OPTIONS": {"timeout": 5},
            "TEST": {"NAME": str(_DATA_DIR / "test_db.sqlite3")},
        }
    }
# WAL mode is activated in CoreConfig.ready() — see core/apps.py

# ── Password validation ─────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalisation ───────────────────────────────────────
LANGUAGE_CODE: str = "en"
TIME_ZONE: str = "Asia/Kolkata"
USE_I18N: bool = True
USE_L10N: bool = True
USE_TZ: bool = True

# 22 Eighth Schedule languages + English
LANGUAGES = [
    ("en",  "English"),
    ("hi",  "हिन्दी (Hindi)"),
    ("bn",  "বাংলা (Bengali)"),
    ("te",  "తెలుగు (Telugu)"),
    ("mr",  "मराठी (Marathi)"),
    ("ta",  "தமிழ் (Tamil)"),
    ("ur",  "اردو (Urdu)"),
    ("gu",  "ગુજરાતી (Gujarati)"),
    ("kn",  "ಕನ್ನಡ (Kannada)"),
    ("ml",  "മലയാളം (Malayalam)"),
    ("or",  "ଓଡ଼ିଆ (Odia)"),
    ("pa",  "ਪੰਜਾਬੀ (Punjabi)"),
    ("as",  "অসমীয়া (Assamese)"),
    ("mai", "मैथिली (Maithili)"),
    ("sat", "ᱥᱟᱱᱛᱟᱲᱤ (Santali)"),
    ("ks",  "كٲشُر (Kashmiri)"),
    ("ne",  "नेपाली (Nepali)"),
    ("sd",  "سنڌي (Sindhi)"),
    ("kok", "कोंकणी (Konkani)"),
    ("doi", "डोगरी (Dogri)"),
    ("mni", "মৈতৈলোন্ (Manipuri)"),
    ("brx", "बर' (Bodo)"),
    ("sa",  "संस्कृतम् (Sanskrit)"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# ── Sessions ───────────────────────────────────────────────────
SESSION_ENGINE: str = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE: int = 86400 * 7          # 7 days
SESSION_COOKIE_HTTPONLY: bool = True
SESSION_COOKIE_SAMESITE: str = "Lax"
SESSION_COOKIE_SECURE: bool = not DEBUG       # HTTPS only in production

# ── CSRF ────────────────────────────────────────────────────────
CSRF_COOKIE_HTTPONLY: bool = False            # JS reads CSRF for HTMX
CSRF_COOKIE_SAMESITE: str = "Lax"
CSRF_COOKIE_SECURE: bool = not DEBUG

# ── Static files ───────────────────────────────────────────────
STATIC_URL: str = "/static/"
STATIC_ROOT: Path = BASE_DIR / "staticfiles"
# No STATICFILES_DIRS needed — each app's static/ is found via INSTALLED_APPS + APP_DIRS
STATICFILES_STORAGE: str = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ── Default primary key ────────────────────────────────────────
DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

# ── Security headers ───────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER: bool = True
X_FRAME_OPTIONS: str = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF: bool = True
if not DEBUG:
    # SIH Waitress demo is HTTP on localhost — only force HTTPS when explicitly enabled.
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "false").lower() in (
        "true", "1", "yes",
    )
    SECURE_HSTS_SECONDS = 31536000 if SECURE_SSL_REDIRECT else 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(SECURE_SSL_REDIRECT)

# Content-Security-Policy (django-csp)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")   # HTMX needs inline
CSP_STYLE_SRC  = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC    = ("'self'", "data:")
CSP_FONT_SRC   = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_INCLUDE_NONCE_IN = ["SCRIPT_SRC"]

# ── Rate limiting ──────────────────────────────────────────────
RATE_LIMIT_ASK_PER_MIN: int = int(os.environ.get("RATE_LIMIT_ASK_PER_MIN", "10"))

# ── AI / RAG settings ──────────────────────────────────────────
OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL: str    = os.environ.get("OLLAMA_MODEL",    "qwen2.5:3b-instruct-q4_K_M")
# Keep modest on Railway CPU — timeout falls back to evidence_only with citations.
OLLAMA_TIMEOUT: float = float(os.environ.get("OLLAMA_TIMEOUT", "75"))
OLLAMA_NUM_PREDICT: int = int(os.environ.get("OLLAMA_NUM_PREDICT", "256"))
# Translation: ollama (demo-safe) | auto (IndicTrans then Ollama) | indictrans
TRANSLATE_BACKEND: str = os.environ.get("TRANSLATE_BACKEND", "auto").strip().lower()

EMBED_MODEL: str  = os.environ.get("EMBED_MODEL",  "BAAI/bge-m3")
EMBED_DEVICE: str = os.environ.get("EMBED_DEVICE", "cpu")

CHROMA_PERSIST_DIR: str = os.environ.get("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))

# DPDP-aligned audit key (rotate per deployment)
AUDIT_HMAC_KEY: str    = os.environ.get("AUDIT_HMAC_KEY",    "CHANGE_THIS_32_CHAR_KEY_IN_PROD!!")
AUDIT_HMAC_KEY_ID: str = os.environ.get("AUDIT_HMAC_KEY_ID", "v1")

# Feature flags
DEMO_MODE: bool = os.environ.get("DEMO_MODE", "True").lower() in ("true", "1", "yes")
# DEMO_MODE=True → RAG pipeline stubbed, placeholder responses returned.
# Set False only after: `ollama pull qwen2.5:7b-instruct-q4_K_M` + corpus indexed.

# ── Logging ─────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
        "simple":  {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "ip_sakti": {"handlers": ["console"], "level": "DEBUG" if DEBUG else "INFO", "propagate": False},
        "ai":       {"handlers": ["console"], "level": "DEBUG" if DEBUG else "INFO", "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

# ── Development overrides ──────────────────────────────────────
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"] if False else []  # enable manually: pip install django-debug-toolbar
    # WhiteNoise finds files faster in dev when this is off
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
