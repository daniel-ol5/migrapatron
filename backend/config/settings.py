"""
Configuración de Django para MigraPatrón IA.

Las credenciales se leen del archivo .env (ver .env.example). Nada sensible
queda escrito en este archivo: es lo que exige RNF-05.
"""

from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- seguridad
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# ---------------------------------------------------------------- apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.m0_usuarios",  # Gestion de Usuarios y Privacidad
    "apps.m1_bitacora",  # Seguimiento y Bitacora Diaria
    "apps.m2_analisis",  # Analisis Inteligente de Datos
    "apps.m3_reportes",  # Explicabilidad y Reportes
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

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

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

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
            ],
        },
    },
]

# ---------------------------------------------------------------- base de datos
# PostgreSQL es la base real. DB_ENGINE=sqlite permite correr la suite de
# pruebas sin levantar un servidor; CI usa postgres:16 de verdad.
_MOTORES = {
    "postgresql": "django.db.backends.postgresql",
    "sqlite": "django.db.backends.sqlite3",
}
_MOTOR = config("DB_ENGINE", default="postgresql")

if _MOTOR == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": _MOTORES["sqlite"],
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": _MOTORES["postgresql"],
            "NAME": config("DB_NAME", default="migrapatron"),
            "USER": config("DB_USER", default="postgres"),
            "PASSWORD": config("DB_PASSWORD", default=""),
            "HOST": config("DB_HOST", default="127.0.0.1"),
            "PORT": config("DB_PORT", default="5432"),
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# El paciente se identifica por email: ver apps/m0_usuarios/models.py
AUTH_USER_MODEL = "m0_usuarios.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------- i18n
LANGUAGE_CODE = "es"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------- estáticos
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------- DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
}

if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += (
        "rest_framework.renderers.BrowsableAPIRenderer",
    )

# ---------------------------------------------------------------- JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("ACCESS_TOKEN_MINUTES", default=15, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("REFRESH_TOKEN_DAYS", default=30, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------------------------------------------------------------- OpenAPI
SPECTACULAR_SETTINGS = {
    "TITLE": "MigraPatrón IA",
    "DESCRIPTION": (
        "API de minería de patrones explicable para pacientes con migraña. "
        "El sistema no diagnostica: muestra asociaciones estadísticas en los "
        "datos del propio paciente."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ---------------------------------------------------------------- CORS
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

if DEBUG:
    # En desarrollo se acepta cualquier puerto de localhost.
    #
    # Flutter web elige un puerto al azar en cada arranque (64241, 51832, ...),
    # asi que una lista fija de puertos obliga a recordar --web-port en cada
    # ejecucion. Olvidarlo produce un error de CORS que no dice que falto: la
    # app carga bien y ninguna peticion funciona.
    #
    # Sigue siendo restrictivo: solo localhost y 127.0.0.1, nunca un dominio
    # externo. Y solo con DEBUG=True, de modo que en produccion rige la lista
    # explicita de arriba.
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://localhost:\d+$",
        r"^http://127\.0\.0\.1:\d+$",
    ]

# ---------------------------------------------------------------- motor
# Parámetros por defecto del motor de patrones. Se pueden sobrescribir por
# petición; quedan guardados en analisis.parametros para que cada corrida sea
# reproducible (RN-06).
MOTOR = {
    "VERSION": "0.1.0",
    # ---- M2.1 criterios minimos de evidencia
    "MINIMO_BITACORAS": 20,
    "MINIMO_EPISODIOS": 3,
    # ---- M2.2 vinculacion temporal
    "VENTANA_HORAS": 48,
    "PERIODO_DIAS": 90,
    # ---- M2.3 filtrado de reglas
    "SOPORTE_MIN": 0.10,
    "CONFIANZA_MIN": 0.60,
    "LIFT_MIN": 1.20,
    "CASOS_MIN": 3,
    "ALFA": 0.05,
    "MAX_ITEMS_ANTECEDENTE": 3,
    "MAX_HALLAZGOS": 10,
}

# ---------------------------------------------------------------- endurecido
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
