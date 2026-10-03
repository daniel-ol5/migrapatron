"""
Configuración para la suite de pruebas.

Por defecto corre sobre SQLite en memoria, para que cualquiera del equipo pueda
ejecutar las pruebas sin levantar un PostgreSQL. El pipeline de CI exporta
DB_ENGINE=postgresql y la misma suite corre contra postgres:16 de verdad, que es
donde se valida el comportamiento del motor real (restricciones, JSONB,
transacciones).

La diferencia está declarada a propósito: una suite que nadie puede correr en su
máquina es una suite que nadie corre.
"""

import os

os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-no-usar-en-produccion")
os.environ.setdefault("DEBUG", "False")

from .settings import *  # noqa: F403,E402

USAR_POSTGRES = os.environ.get("DB_ENGINE") == "postgresql"

if not USAR_POSTGRES:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# El endurecido de producción se apaga aquí. Con DEBUG=False, settings.py activa
# SECURE_SSL_REDIRECT, y el cliente de pruebas habla http: cada petición
# respondería 301 hacia https en lugar de ejecutar la vista.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Hasher rápido SOLO para pruebas. Con el PBKDF2 de producción la suite tarda
# tres minutos, casi todo en cifrar contraseñas de usuarios de prueba.
#
# Qué se sigue verificando: que la contraseña no se guarda en claro y que
# check_password funciona (HU-01). Qué deja de cubrirse: nada, porque
# settings.py no toca PASSWORD_HASHERS y producción usa el PBKDF2 de Django.
# Si algún día se cambia el hasher real, hay que hacerlo en settings.py, donde
# esta línea no interfiere.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# El validador de contraseñas se mantiene activo: hay pruebas que verifican
# justamente que una contraseña débil se rechaza (HU-01).
