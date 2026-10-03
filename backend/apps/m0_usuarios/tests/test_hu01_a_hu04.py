"""
Pruebas de M0 - HU-01 a HU-04.

Cada prueba verifica una postcondición del documento, no solo que la petición
devuelva 200.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.m0_usuarios.models import (
    AvisoPrivacidad,
    Consentimiento,
    EventoAuditoria,
    PerfilClinico,
    Usuario,
)

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------- fixtures
@pytest.fixture
def aviso():
    return AvisoPrivacidad.objects.create(
        version="1.0",
        titulo="Aviso de prueba",
        contenido="Texto del aviso.",
        es_actual=True,
    )


@pytest.fixture
def cliente():
    return APIClient()


@pytest.fixture
def datos_registro(aviso):
    return {
        "email": "paciente@ejemplo.com",
        "password": "ClaveSegura.2026",
        "nombre": "Ana",
        "apellido": "Pérez",
        "acepta_aviso": True,
        "version_aviso": aviso.version,
    }


@pytest.fixture
def usuario(aviso):
    u = Usuario.objects.create_user(
        email="paciente@ejemplo.com",
        password="ClaveSegura.2026",
        nombre="Ana",
        apellido="Pérez",
    )
    PerfilClinico.objects.create(usuario=u)
    Consentimiento.objects.create(usuario=u, aviso=aviso, aceptado=True)
    return u


@pytest.fixture
def autenticado(cliente, usuario):
    respuesta = cliente.post(
        reverse("m0_usuarios:login"),
        {"email": usuario.email, "password": "ClaveSegura.2026"},
        format="json",
    )
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.data['access']}")
    cliente.refresh_token = respuesta.data["refresh"]
    return cliente


# ============================================================ HU-01 Registro
class TestHU01Registro:
    def test_crea_usuario_perfil_y_consentimiento(self, cliente, datos_registro):
        respuesta = cliente.post(
            reverse("m0_usuarios:registro"), datos_registro, format="json"
        )

        assert respuesta.status_code == 201
        usuario = Usuario.objects.get(email="paciente@ejemplo.com")
        assert usuario.is_active
        assert PerfilClinico.objects.filter(usuario=usuario).exists()
        assert usuario.consintio_analisis

    def test_conserva_la_version_consentida(self, cliente, datos_registro, aviso):
        cliente.post(reverse("m0_usuarios:registro"), datos_registro, format="json")

        hecho = Consentimiento.objects.get(usuario__email="paciente@ejemplo.com")
        assert hecho.aviso == aviso
        assert hecho.aceptado is True
        assert hecho.otorgado_en is not None

    def test_la_contrasena_queda_cifrada(self, cliente, datos_registro):
        cliente.post(reverse("m0_usuarios:registro"), datos_registro, format="json")

        usuario = Usuario.objects.get(email="paciente@ejemplo.com")
        assert usuario.password != "ClaveSegura.2026"
        assert usuario.check_password("ClaveSegura.2026")

    def test_normaliza_el_email_a_minusculas(self, cliente, datos_registro):
        datos_registro["email"] = "Paciente@Ejemplo.COM"
        cliente.post(reverse("m0_usuarios:registro"), datos_registro, format="json")

        assert Usuario.objects.filter(email="paciente@ejemplo.com").exists()

    def test_rechaza_email_duplicado(self, cliente, datos_registro, usuario):
        respuesta = cliente.post(
            reverse("m0_usuarios:registro"), datos_registro, format="json"
        )

        assert respuesta.status_code == 400
        assert Usuario.objects.filter(email="paciente@ejemplo.com").count() == 1

    def test_rechaza_si_no_acepta_el_aviso(self, cliente, datos_registro):
        datos_registro["acepta_aviso"] = False
        respuesta = cliente.post(
            reverse("m0_usuarios:registro"), datos_registro, format="json"
        )

        assert respuesta.status_code == 400
        assert not Usuario.objects.exists()

    def test_rechaza_una_version_de_aviso_que_ya_no_rige(self, cliente, datos_registro):
        """Aceptar un texto que dejó de estar vigente no es consentir."""
        AvisoPrivacidad.objects.create(
            version="2.0", titulo="Nuevo", contenido="Otro texto.", es_actual=True
        )

        respuesta = cliente.post(
            reverse("m0_usuarios:registro"), datos_registro, format="json"
        )

        assert respuesta.status_code == 400
        assert not Usuario.objects.exists()

    def test_rechaza_contrasena_debil(self, cliente, datos_registro):
        datos_registro["password"] = "12345678"
        respuesta = cliente.post(
            reverse("m0_usuarios:registro"), datos_registro, format="json"
        )

        assert respuesta.status_code == 400

    def test_deja_asiento_de_auditoria(self, cliente, datos_registro):
        cliente.post(reverse("m0_usuarios:registro"), datos_registro, format="json")

        assert EventoAuditoria.objects.filter(
            accion=EventoAuditoria.Accion.REGISTRO
        ).exists()


# ======================================================== HU-02 Inicio sesión
class TestHU02Login:
    def test_devuelve_tokens_y_usuario(self, cliente, usuario):
        respuesta = cliente.post(
            reverse("m0_usuarios:login"),
            {"email": usuario.email, "password": "ClaveSegura.2026"},
            format="json",
        )

        assert respuesta.status_code == 200
        assert "access" in respuesta.data
        assert "refresh" in respuesta.data
        assert respuesta.data["usuario"]["email"] == usuario.email

    def test_informa_el_estado_del_consentimiento(self, cliente, usuario):
        respuesta = cliente.post(
            reverse("m0_usuarios:login"),
            {"email": usuario.email, "password": "ClaveSegura.2026"},
            format="json",
        )

        assert respuesta.data["usuario"]["consintio_analisis"] is True

    def test_actualiza_ultimo_acceso(self, cliente, usuario):
        assert usuario.ultimo_acceso is None

        cliente.post(
            reverse("m0_usuarios:login"),
            {"email": usuario.email, "password": "ClaveSegura.2026"},
            format="json",
        )

        usuario.refresh_from_db()
        assert usuario.ultimo_acceso is not None

    def test_el_error_no_revela_si_el_email_existe(self, cliente, usuario):
        """Distinguirlos permitiría enumerar cuentas de una app de salud."""
        inexistente = cliente.post(
            reverse("m0_usuarios:login"),
            {"email": "nadie@ejemplo.com", "password": "ClaveSegura.2026"},
            format="json",
        )
        mal_password = cliente.post(
            reverse("m0_usuarios:login"),
            {"email": usuario.email, "password": "EquivocadaTotal.9"},
            format="json",
        )

        assert inexistente.status_code == mal_password.status_code == 400
        assert str(inexistente.data) == str(mal_password.data)

    def test_registra_el_intento_fallido(self, cliente, usuario):
        cliente.post(
            reverse("m0_usuarios:login"),
            {"email": usuario.email, "password": "EquivocadaTotal.9"},
            format="json",
        )

        assert EventoAuditoria.objects.filter(
            accion=EventoAuditoria.Accion.ACCESO_FALLIDO
        ).exists()

    def test_cuenta_desactivada_no_inicia_sesion(self, cliente, usuario):
        usuario.is_active = False
        usuario.save()

        respuesta = cliente.post(
            reverse("m0_usuarios:login"),
            {"email": usuario.email, "password": "ClaveSegura.2026"},
            format="json",
        )

        assert respuesta.status_code == 400


# ========================================================= HU-03 Cierre sesión
class TestHU03Logout:
    def test_cierra_la_sesion_por_post(self, autenticado):
        respuesta = autenticado.post(
            reverse("m0_usuarios:logout"),
            {"refresh": autenticado.refresh_token},
            format="json",
        )

        assert respuesta.status_code == 204

    def test_el_token_ya_no_sirve_despues(self, autenticado):
        autenticado.post(
            reverse("m0_usuarios:logout"),
            {"refresh": autenticado.refresh_token},
            format="json",
        )

        reintento = autenticado.post(
            reverse("m0_usuarios:refresh"),
            {"refresh": autenticado.refresh_token},
            format="json",
        )
        assert reintento.status_code == 401

    def test_get_no_cierra_la_sesion(self, autenticado):
        """Si GET cerrara sesión, un enlace o una imagen remota bastaría."""
        respuesta = autenticado.get(reverse("m0_usuarios:logout"))

        assert respuesta.status_code == 405

    def test_no_borra_datos_del_paciente(self, autenticado, usuario):
        autenticado.post(
            reverse("m0_usuarios:logout"),
            {"refresh": autenticado.refresh_token},
            format="json",
        )

        assert Usuario.objects.filter(pk=usuario.pk).exists()
        assert usuario.consentimientos.exists()

    def test_sin_sesion_no_se_puede_cerrar(self, cliente):
        respuesta = cliente.post(reverse("m0_usuarios:logout"), {}, format="json")

        assert respuesta.status_code == 401


# ============================================= HU-04 Perfil y consentimiento
class TestHU04Perfil:
    def test_consulta_el_perfil_propio(self, autenticado, usuario):
        respuesta = autenticado.get(reverse("m0_usuarios:perfil"))

        assert respuesta.status_code == 200
        assert respuesta.data["email"] == usuario.email
        assert "perfil" in respuesta.data

    def test_actualiza_datos_clinicos(self, autenticado, usuario):
        respuesta = autenticado.patch(
            reverse("m0_usuarios:perfil"),
            {"anios_con_migrana": 7, "tipo_migrana": "CON_AURA", "nombre": "Ana María"},
            format="json",
        )

        assert respuesta.status_code == 200
        usuario.refresh_from_db()
        assert usuario.nombre == "Ana María"
        assert usuario.perfil.anios_con_migrana == 7
        assert usuario.perfil.tipo_migrana == "CON_AURA"

    def test_el_email_no_cambia_por_esta_via(self, autenticado, usuario):
        autenticado.patch(
            reverse("m0_usuarios:perfil"),
            {"email": "otro@ejemplo.com"},
            format="json",
        )

        usuario.refresh_from_db()
        assert usuario.email == "paciente@ejemplo.com"

    def test_sin_sesion_no_hay_perfil(self, cliente):
        assert cliente.get(reverse("m0_usuarios:perfil")).status_code == 401


class TestHU04HistorialConsentimiento:
    def test_retirar_agrega_un_hecho_sin_borrar_el_anterior(self, autenticado, usuario):
        antes = usuario.consentimientos.count()

        respuesta = autenticado.post(
            reverse("m0_usuarios:consentimiento"), {"aceptado": False}, format="json"
        )

        assert respuesta.status_code == 201
        assert usuario.consentimientos.count() == antes + 1
        # El hecho original sigue ahí, intacto.
        assert usuario.consentimientos.filter(aceptado=True).exists()

    def test_tras_retirar_el_consentimiento_vigente_es_falso(self, autenticado, usuario):
        autenticado.post(
            reverse("m0_usuarios:consentimiento"), {"aceptado": False}, format="json"
        )

        usuario.refresh_from_db()
        assert usuario.consintio_analisis is False

    def test_se_puede_volver_a_otorgar(self, autenticado, usuario, aviso):
        autenticado.post(
            reverse("m0_usuarios:consentimiento"), {"aceptado": False}, format="json"
        )
        autenticado.post(
            reverse("m0_usuarios:consentimiento"),
            {"aceptado": True, "version_aviso": aviso.version},
            format="json",
        )

        usuario.refresh_from_db()
        assert usuario.consintio_analisis is True
        assert usuario.consentimientos.count() == 3

    def test_el_historial_se_devuelve_completo(self, autenticado):
        autenticado.post(
            reverse("m0_usuarios:consentimiento"), {"aceptado": False}, format="json"
        )

        respuesta = autenticado.get(reverse("m0_usuarios:consentimiento"))

        assert respuesta.status_code == 200
        assert respuesta.data["vigente"] is False
        assert len(respuesta.data["historial"]) == 2

    def test_no_se_puede_retirar_dos_veces(self, autenticado):
        autenticado.post(
            reverse("m0_usuarios:consentimiento"), {"aceptado": False}, format="json"
        )
        segundo = autenticado.post(
            reverse("m0_usuarios:consentimiento"), {"aceptado": False}, format="json"
        )

        assert segundo.status_code == 400


# ================================================== M0.4 Eliminación de cuenta
class TestBajaCuenta:
    def test_elimina_la_cuenta_y_sus_datos(self, autenticado, usuario):
        respuesta = autenticado.post(
            reverse("m0_usuarios:baja"),
            {"password": "ClaveSegura.2026", "confirmacion": "ELIMINAR"},
            format="json",
        )

        assert respuesta.status_code == 200
        assert not Usuario.objects.filter(pk=usuario.pk).exists()
        assert not PerfilClinico.objects.filter(usuario_id=usuario.pk).exists()

    def test_exige_la_contrasena(self, autenticado, usuario):
        respuesta = autenticado.post(
            reverse("m0_usuarios:baja"),
            {"password": "EquivocadaTotal.9", "confirmacion": "ELIMINAR"},
            format="json",
        )

        assert respuesta.status_code == 400
        assert Usuario.objects.filter(pk=usuario.pk).exists()

    def test_exige_la_confirmacion_escrita(self, autenticado, usuario):
        respuesta = autenticado.post(
            reverse("m0_usuarios:baja"),
            {"password": "ClaveSegura.2026", "confirmacion": "si"},
            format="json",
        )

        assert respuesta.status_code == 400
        assert Usuario.objects.filter(pk=usuario.pk).exists()

    def test_el_asiento_de_auditoria_sobrevive_al_borrado(self, autenticado, usuario):
        """El borrado tiene que quedar rastreable aunque la fila ya no exista."""
        autenticado.post(
            reverse("m0_usuarios:baja"),
            {"password": "ClaveSegura.2026", "confirmacion": "ELIMINAR"},
            format="json",
        )

        asiento = EventoAuditoria.objects.filter(
            accion=EventoAuditoria.Accion.BAJA_CUENTA
        ).first()
        assert asiento is not None
        assert asiento.email_actor == "paciente@ejemplo.com"
        assert asiento.usuario is None  # SET_NULL al borrar la cuenta
