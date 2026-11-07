"""
Módulo M2 - Suficiencia de Datos (RF-07A y RF-07B / HU-10).

Verifica que el historial del paciente alcance los umbrales mínimos no negociables
antes de habilitar la estimación de riesgo personal mediante regresión logística L2.

Umbrales requeridos por la documentación:
- Mínimo 60 días de bitácora válida.
- Mínimo 6 observaciones/días con episodio de migraña.
- Mínimo 6 observaciones/días sin episodio de migraña.
"""

from apps.m1_bitacora.models import Episodio, RegistroDiario

UMBRAL_MIN_BITACORAS = 60
UMBRAL_MIN_EPISODIOS = 6
UMBRAL_MIN_SIN_EPISODIOS = 6


def verificar_suficiencia_datos(usuario):
    """
    Evalúa si el paciente cuenta con historial suficiente para entrenar el modelo.

    Retorna un diccionario estructurado con:
    - cumple: bool (True solo si cumple todos los mínimos)
    - dias_validos: cantidad de bitácoras completas registradas
    - meta_dias: 60
    - faltan_dias: días restantes para alcanzar la meta
    - dias_con_episodio: cantidad de días con episodio registrado
    - dias_sin_episodio: cantidad de días sin episodio registrado
    - meta_episodios: 6
    - faltan_episodios: episodios restantes para el balance mínimo
    - barra_avance_pct: porcentaje de avance de bitácoras (0.0 a 100.0)
    - mensaje: descripción clara de disponibilidad o de lo que falta
    """
    registros = RegistroDiario.objects.filter(usuario=usuario)
    dias_validos = registros.count()

    # Días con episodio dentro de las fechas registradas
    fechas_con_episodio = set(
        Episodio.objects.filter(
            usuario=usuario,
            registro_diario__isnull=False,
        ).values_list("registro_diario__fecha", flat=True)
    )

    # También considerar episodios cuya fecha local coincide con alguna bitácora
    if not fechas_con_episodio:
        episodios = Episodio.objects.filter(usuario=usuario)
        fechas_registros = set(registros.values_list("fecha", flat=True))
        for ep in episodios:
            fecha_ep = ep.inicio.date()
            if fecha_ep in fechas_registros:
                fechas_con_episodio.add(fecha_ep)

    total_con_episodio = len(fechas_con_episodio)
    total_sin_episodio = max(0, dias_validos - total_con_episodio)

    cumple_dias = dias_validos >= UMBRAL_MIN_BITACORAS
    cumple_con_ep = total_con_episodio >= UMBRAL_MIN_EPISODIOS
    cumple_sin_ep = total_sin_episodio >= UMBRAL_MIN_SIN_EPISODIOS

    cumple = cumple_dias and cumple_con_ep and cumple_sin_ep

    faltan_dias = max(0, UMBRAL_MIN_BITACORAS - dias_validos)
    faltan_ep = max(0, UMBRAL_MIN_EPISODIOS - total_con_episodio)
    faltan_sin_ep = max(0, UMBRAL_MIN_SIN_EPISODIOS - total_sin_episodio)

    barra_pct = round(min(1.0, dias_validos / UMBRAL_MIN_BITACORAS) * 100, 1)

    if cumple:
        mensaje = (
            f"Historial suficiente ({dias_validos} días, {total_con_episodio} episodios). "
            "Modelo supervisado L2 disponible."
        )
    else:
        partes_faltantes = []
        if faltan_dias > 0:
            partes_faltantes.append(f"{faltan_dias} días de bitácora")
        if faltan_ep > 0:
            partes_faltantes.append(f"{faltan_ep} días con episodio")
        if faltan_sin_ep > 0:
            partes_faltantes.append(f"{faltan_sin_ep} días sin episodio")
        mensaje = (
            f"Se requieren al menos {UMBRAL_MIN_BITACORAS} días de bitácora válida "
            f"y balance mínimo de clases ({UMBRAL_MIN_EPISODIOS} con episodio y {UMBRAL_MIN_SIN_EPISODIOS} sin episodio). "
            f"Te faltan: {', '.join(partes_faltantes)}."
        )

    return {
        "cumple": cumple,
        "dias_validos": dias_validos,
        "meta_dias": UMBRAL_MIN_BITACORAS,
        "faltan_dias": faltan_dias,
        "dias_con_episodio": total_con_episodio,
        "meta_episodios": UMBRAL_MIN_EPISODIOS,
        "faltan_episodios": faltan_ep,
        "dias_sin_episodio": total_sin_episodio,
        "meta_sin_episodio": UMBRAL_MIN_SIN_EPISODIOS,
        "faltan_sin_episodio": faltan_sin_ep,
        "barra_avance_pct": barra_pct,
        "mensaje": mensaje,
    }
