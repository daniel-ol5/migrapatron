"""
Pruebas de HU-17 / RF-14: Alerta de Bandera Roja para Cefalea en Trueno.
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.m0_usuarios.models import (
    AvisoPrivacidad,
    Consentimiento,
    EventoAuditoria,
    PerfilClinico,
    Usuario,
)
from apps.m1_bitacora.models import AlertaBanderaRoja

pytestmark = pytest.mark.django_db


def crear_paciente(email):
    usuario = Usuario.objects.create_user(
        email=email, password="ClaveSegura.2026", nombre="Test", apellido="Paciente"
    )
    PerfilClinico.objects.create(usuario=usuario)
    aviso = AvisoPrivacidad.objects.filter(es_actual=True).first() or (
        AvisoPrivacidad.objects.create(
            version="1.0", titulo="Aviso", contenido="Texto.", es_actual=True
        )
    )
    Consentimiento.objects.create(usuario=usuario, aviso=aviso, aceptado=True)
    return usuario


def cliente_de(usuario):
    cliente = APIClient()
    respuesta = cliente.post(
        reverse("m0_usuarios:login"),
        {"email": usuario.email, "password": "ClaveSegura.2026"},
        format="json",
    )
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.data['access']}")
    return cliente


class TestHU17BanderaRoja:
    """Verifica detección de bandera roja clínica y aislamiento de alertas."""

    def test_disparo_alerta_intensidad_10_inicio_subito(self):
        """TC-M4-01: intensidad 10 + inicio súbito genera alerta urgente y rastro de auditoría."""
        usuario = crear_paciente("paciente.trueno@test.com")
        cliente = cliente_de(usuario)

        payload = {
            "inicio": timezone.now().isoformat(),
            "duracion_min": 120,
            "intensidad": 10,
            "inicio_subito": True,
            "nauseas": True,
            "sensibilidad_luz": True,
        }

        resp = cliente.post(reverse("m1_bitacora:episodio-lista"), payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

        data = resp.data
        assert data["alerta_bandera_roja"] is not None
        assert "urgente" in data["alerta_bandera_roja"]["mensaje"].lower()
        assert not data["alerta_bandera_roja"]["confirmada"]

        # Verificar rastro de auditoría
        asiento = EventoAuditoria.objects.filter(
            usuario=usuario, accion=EventoAuditoria.Accion.ALERTA_BANDERA_ROJA
        ).first()
        assert asiento is not None

    def test_no_dispara_con_intensidad_menor(self):
        """Intensidad 9 con inicio súbito no dispara bandera roja."""
        usuario = crear_paciente("paciente.leve@test.com")
        cliente = cliente_de(usuario)

        payload = {
            "inicio": timezone.now().isoformat(),
            "duracion_min": 60,
            "intensidad": 9,
            "inicio_subito": True,
            "nauseas": True,
        }

        resp = cliente.post(reverse("m1_bitacora:episodio-lista"), payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["alerta_bandera_roja"] is None

    def test_no_dispara_sin_inicio_subito(self):
        """Intensidad 10 de inicio progresivo no dispara bandera roja de trueno."""
        usuario = crear_paciente("paciente.progresivo@test.com")
        cliente = cliente_de(usuario)

        payload = {
            "inicio": timezone.now().isoformat(),
            "duracion_min": 60,
            "intensidad": 10,
            "inicio_subito": False,
            "nauseas": True,
        }

        resp = cliente.post(reverse("m1_bitacora:episodio-lista"), payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["alerta_bandera_roja"] is None

    def test_confirmar_lectura_alerta(self):
        """El paciente puede confirmar que leyó la orientación médica."""
        usuario = crear_paciente("paciente.confirma@test.com")
        cliente = cliente_de(usuario)

        payload = {
            "inicio": timezone.now().isoformat(),
            "duracion_min": 60,
            "intensidad": 10,
            "inicio_subito": True,
        }
        resp = cliente.post(reverse("m1_bitacora:episodio-lista"), payload, format="json")
        alerta_id = resp.data["alerta_bandera_roja"]["id"]

        resp_conf = cliente.post(
            reverse("m1_bitacora:alerta-confirmar", kwargs={"pk": alerta_id}),
            format="json",
        )
        assert resp_conf.status_code == status.HTTP_200_OK
        assert resp_conf.data["confirmada"] is True

        alerta_db = AlertaBanderaRoja.objects.get(pk=alerta_id)
        assert alerta_db.confirmada is True

    def test_aislamiento_no_confirmar_alerta_ajena(self):
        """Un usuario ajeno recibe 404 al intentar confirmar una alerta de otro paciente."""
        usuario_a = crear_paciente("paciente.a@test.com")
        usuario_b = crear_paciente("paciente.b@test.com")
        cliente_a = cliente_de(usuario_a)
        cliente_b = cliente_de(usuario_b)

        resp = cliente_a.post(
            reverse("m1_bitacora:episodio-lista"),
            {
                "inicio": timezone.now().isoformat(),
                "duracion_min": 60,
                "intensidad": 10,
                "inicio_subito": True,
            },
            format="json",
        )
        alerta_id = resp.data["alerta_bandera_roja"]["id"]

        # Usuario B intenta confirmar alerta de Usuario A
        resp_ajeno = cliente_b.post(
            reverse("m1_bitacora:alerta-confirmar", kwargs={"pk": alerta_id}),
            format="json",
        )
        assert resp_ajeno.status_code == status.HTTP_404_NOT_FOUND
