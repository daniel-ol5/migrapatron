"""
Pruebas del Módulo Principal M2 (HU-10, HU-11, HU-18):
- RF-07A y RF-07B: Bloqueo estricto por <60 días y balance de clases.
- RF-08A a RF-08C: Ventanas temporales y modelo de Regresión Logística L2.
- RF-09A a RF-09C: Tarjeta visual, hasta 3 factores en lenguaje no causal y divulgación progresiva.
- RF-15 / HU-18: Prevención de cefalea por uso excesivo de medicación (>10 días en 30 días).
"""

from datetime import time, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.m0_usuarios.models import (
    AvisoPrivacidad,
    Consentimiento,
    PerfilClinico,
    Usuario,
)
from apps.m1_bitacora.models import Episodio, RegistroDiario
from apps.m2_analisis.models import Analisis, EstimacionRiesgo

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


def sembrar_historial(usuario, total_dias=65, dias_con_episodio=10, dias_con_rescate=5):
    """Genera una serie cronológica sintética válida para pruebas."""
    hoy = timezone.localdate()
    fecha_inicio = hoy - timedelta(days=total_dias - 1)

    registros = []
    for i in range(total_dias):
        f = fecha_inicio + timedelta(days=i)
        es_dia_rescate = i >= (total_dias - dias_con_rescate)
        reg = RegistroDiario.objects.create(
            usuario=usuario,
            fecha=f,
            hora_corte=time(22, 0),
            horas_sueno=5.5 if (i % 5 == 0) else 7.5,
            hidratacion="MEDIA",
            comida_omitida=1 if (i % 6 == 0) else 0,
            estres=4 if (i % 4 == 0) else 2,
            horas_pantalla=8.0 if (i % 3 == 0) else 5.0,
            minutos_actividad=15 if (i % 5 == 0) else 45,
            cafeina_tazas=2,
            medicacion_rescate=es_dia_rescate,
            completado=True,
        )
        registros.append(reg)

    # Sembrar episodios distribuidos en días específicos
    paso = max(1, total_dias // dias_con_episodio)
    episodios_creados = 0
    for i in range(0, total_dias, paso):
        if episodios_creados >= dias_con_episodio:
            break
        reg = registros[i]
        dt_inicio = timezone.make_aware(timezone.datetime.combine(reg.fecha, time(14, 0)))
        Episodio.objects.create(
            usuario=usuario,
            registro_diario=reg,
            inicio=dt_inicio,
            duracion_min=180,
            intensidad=7,
            nauseas=True,
            sensibilidad_luz=True,
        )
        episodios_creados += 1


class TestM2SuficienciaYBloqueo:
    """RF-07A y RF-07B (TC-M2-01 / TC-P01)."""

    def test_bloqueo_con_menos_de_60_dias(self):
        """Con historial insuficiente (<60 días) la estimación se bloquea y retorna días_validos / 60."""
        usuario = crear_paciente("insuficiente.dias@test.com")
        cliente = cliente_de(usuario)

        # Sembrar solo 20 días
        sembrar_historial(usuario, total_dias=20, dias_con_episodio=4)

        resp = cliente.post(reverse("m2_analisis:analisis-ejecutar"), format="json")
        assert resp.status_code == status.HTTP_200_OK

        data = resp.data
        assert data["estado"] == "DATOS_INSUFICIENTES"
        assert data["suficiencia"]["cumple"] is False
        assert data["suficiencia"]["dias_validos"] == 20
        assert data["suficiencia"]["meta_dias"] == 60
        assert data["suficiencia"]["faltan_dias"] == 40
        assert data["suficiencia"]["barra_avance_pct"] == 33.3
        assert data["estimacion"] is None

    def test_bloqueo_por_falta_de_balance_de_clases(self):
        """Con 60 días pero menos de 6 episodios, se bloquea por falta de balance."""
        usuario = crear_paciente("insuficiente.balance@test.com")
        cliente = cliente_de(usuario)

        # 60 días pero solo 2 episodios
        sembrar_historial(usuario, total_dias=60, dias_con_episodio=2)

        resp = cliente.post(reverse("m2_analisis:analisis-ejecutar"), format="json")
        assert resp.status_code == status.HTTP_200_OK

        data = resp.data
        assert data["estado"] == "DATOS_INSUFICIENTES"
        assert data["suficiencia"]["cumple"] is False
        assert data["suficiencia"]["dias_con_episodio"] == 2
        assert data["suficiencia"]["faltan_episodios"] == 4


class TestM2PrediccionSupervisadaL2:
    """RF-08A a RF-09C (TC-M2-01 / TC-P02)."""

    def test_ejecucion_exitosa_con_datos_suficientes(self):
        """Con >=60 días y balance válido, entrena L2, calcula métricas y genera estimación."""
        usuario = crear_paciente("suficiente.l2@test.com")
        cliente = cliente_de(usuario)

        sembrar_historial(usuario, total_dias=65, dias_con_episodio=12)

        resp = cliente.post(
            reverse("m2_analisis:analisis-ejecutar"),
            {"horizonte_horas": 48},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED

        data = resp.data
        assert data["estado"] == "OK"
        assert data["suficiencia"]["cumple"] is True

        # Estimación y tarjeta visual
        estimacion = data["estimacion"]
        assert estimacion is not None
        assert estimacion["categoria_visual"] in ["BAJO", "MODERADO", "ELEVADO"]
        assert 0.0 <= float(estimacion["probabilidad"]) <= 1.0
        assert estimacion["horizonte_horas"] == 48

        # Hasta 3 factores en lenguaje no causal (RF-09B)
        factores = estimacion["factores_principales"]
        assert len(factores) <= 3
        for f in factores:
            assert (
                "coincidió" in f["explicacion"].lower()
                or "registros" in f["explicacion"].lower()
            )

        # Deslinde y advertencia médica obligatoria
        assert "no demuestra causalidad" in data["advertencia"].lower()

        # Métricas técnicas de validación interna (RF-09C)
        metricas = data["metricas_tecnicas"]
        assert "auc_roc" in metricas
        assert "brier_score" in metricas
        assert metricas["tamano_entrenamiento"] > 0
        assert metricas["tamano_validacion"] > 0

        # Verificación de persistencia en base de datos
        analisis_db = Analisis.objects.filter(
            usuario=usuario, estado=Analisis.Estado.OK
        ).first()
        assert analisis_db is not None
        assert EstimacionRiesgo.objects.filter(analisis=analisis_db).exists()


class TestM3AlertaMedicacionRescate:
    """HU-18 / RF-15 (TC-M3-06)."""

    def test_alerta_sobreuso_medicacion_al_superar_10_dias(self):
        """Si registra rescate en >10 días en el último mes, emite advertencia preventiva."""
        usuario = crear_paciente("rescate.alerta@test.com")
        cliente = cliente_de(usuario)

        # Sembrar 65 días con 14 días de medicación de rescate en los últimos 30 días
        sembrar_historial(
            usuario, total_dias=65, dias_con_episodio=8, dias_con_rescate=14
        )

        resp = cliente.get(reverse("m2_analisis:analisis-medicacion"))
        assert resp.status_code == status.HTTP_200_OK

        data = resp.data
        assert data["total_dias_rescate_30d"] == 14
        assert data["alerta_activa"] is True
        assert "más de 10 días" in data["mensaje"]
        assert "no suspendas ni modifiques medicamentos" in data["mensaje"].lower()


class TestM2ConsultasYAislamiento:
    """Verifica endpoints de consulta y aislamiento estricto por cuenta."""

    def test_consulta_suficiencia_y_ultimo_analisis(self):
        """El paciente puede consultar su estado de suficiencia y su última estimación."""
        usuario = crear_paciente("paciente.consulta@test.com")
        cliente = cliente_de(usuario)

        sembrar_historial(usuario, total_dias=65, dias_con_episodio=10)

        # Ejecutar análisis
        cliente.post(reverse("m2_analisis:analisis-ejecutar"), format="json")

        # Consultar suficiencia
        resp_suf = cliente.get(reverse("m2_analisis:analisis-suficiencia"))
        assert resp_suf.status_code == status.HTTP_200_OK
        assert resp_suf.data["cumple"] is True

        # Consultar último análisis
        resp_ult = cliente.get(reverse("m2_analisis:analisis-ultimo"))
        assert resp_ult.status_code == status.HTTP_200_OK
        assert resp_ult.data["estado"] == "OK"
        assert resp_ult.data["estimacion"] is not None

    def test_aislamiento_entre_usuarios(self):
        """Usuario B no ve las estimaciones de Usuario A."""
        usuario_a = crear_paciente("paciente.aisla.a@test.com")
        usuario_b = crear_paciente("paciente.aisla.b@test.com")
        cliente_a = cliente_de(usuario_a)
        cliente_b = cliente_de(usuario_b)

        sembrar_historial(usuario_a, total_dias=65, dias_con_episodio=10)
        cliente_a.post(reverse("m2_analisis:analisis-ejecutar"), format="json")

        # Usuario B aún no tiene registros ni análisis
        resp_b = cliente_b.get(reverse("m2_analisis:analisis-ultimo"))
        assert resp_b.status_code == status.HTTP_200_OK
        assert resp_b.data["estimacion"] is None
        assert resp_b.data["suficiencia"]["dias_validos"] == 0
