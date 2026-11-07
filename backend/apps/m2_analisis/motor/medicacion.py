"""
Módulo M3 / M4 - Control de Medicación de Rescate (HU-18 / RF-15).

Contabiliza fechas distintas en las que el paciente registró consumo de analgésicos
o triptanes de rescate en una ventana móvil de 30 días.
Si el total supera los 10 días, emite una advertencia preventiva de no causalidad
según los criterios clínicos de ICHD-3 sobre sospecha de cefalea por sobreuso.
"""

from datetime import timedelta

from django.utils import timezone

from apps.m1_bitacora.models import RegistroDiario

UMBRAL_DIAS_MEDICACION = 10
VENTANA_DIAS_MEDICACION = 30


def contar_dias_rescate_30d(usuario, fecha_referencia=None):
    """
    Cuenta los días distintos con medicación de rescate en los últimos 30 días.

    Retorna un diccionario con:
    - total_dias_rescate: número de fechas distintas con medicación
    - umbral_maximo: 10
    - alerta_activa: True si total_dias_rescate > 10
    - mensaje: advertencia preventiva con deslinde clínico o aviso informativo
    """
    if fecha_referencia is None:
        fecha_referencia = timezone.localdate()

    desde = fecha_referencia - timedelta(days=VENTANA_DIAS_MEDICACION - 1)

    fechas_con_medicacion = set(
        RegistroDiario.objects.filter(
            usuario=usuario,
            fecha__gte=desde,
            fecha__lte=fecha_referencia,
            medicacion_rescate=True,
        ).values_list("fecha", flat=True)
    )

    total_dias = len(fechas_con_medicacion)
    alerta_activa = total_dias > UMBRAL_DIAS_MEDICACION

    if alerta_activa:
        mensaje = (
            f"Registraste medicación de rescate en más de 10 días durante los últimos 30 días "
            f"({total_dias} días registrados; el límite preventivo es {UMBRAL_DIAS_MEDICACION} días). "
            "Conversa este dato con tu profesional de salud. "
            "No suspendas ni modifiques medicamentos por esta alerta."
        )
    else:
        mensaje = (
            f"Registraste medicación de rescate en {total_dias} de los últimos 30 días "
            f"(límite preventivo de observación: {UMBRAL_DIAS_MEDICACION} días)."
        )

    return {
        "total_dias_rescate_30d": total_dias,
        "umbral_maximo": UMBRAL_DIAS_MEDICACION,
        "alerta_activa": alerta_activa,
        "mensaje": mensaje,
    }
