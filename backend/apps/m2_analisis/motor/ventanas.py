"""
Módulo M2 - Construcción de Ventanas Temporales (RF-08A y RF-08B / HU-10).

Prepara la matriz de características y la variable objetivo para la regresión logística L2.
Reglas clave:
- Ventana temporal móvil de 24, 48 o 72 horas tras la hora de corte de la bitácora.
- Promedios móviles de 30 días previos y deltas de variación.
- Frecuencia de episodios en 7, 14 y 30 días previos.
- Prevención estricta de fuga temporal (Data Leakage): ningún dato posterior
  a la fecha/hora de corte se incluye en las características de entrada.
"""

from datetime import datetime, time, timedelta

import numpy as np
import pandas as pd
from django.utils import timezone

from apps.m1_bitacora.models import Episodio, RegistroDiario

MAPA_HIDRATACION = {
    "BAJA": 1.0,
    "MEDIA": 2.0,
    "ALTA": 3.0,
    "": 2.0,
}


def construir_matriz_temporal(usuario, horizonte_horas=48):
    """
    Construye el conjunto de datos (X, y, df_metadata) ordenado cronológicamente.

    Parámetros:
    - usuario: Usuario propietario
    - horizonte_horas: 24, 48 o 72 horas para definir el objetivo Y

    Retorna:
    - df_caracteristicas (pd.DataFrame): X
    - serie_objetivo (pd.Series): y (0 o 1)
    - df_completo (pd.DataFrame): X + y + metadatos (fecha, hora_corte, etc.)
    """
    registros = list(RegistroDiario.objects.filter(usuario=usuario).order_by("fecha"))
    if not registros:
        return pd.DataFrame(), pd.Series(dtype=int), pd.DataFrame()

    episodios = list(Episodio.objects.filter(usuario=usuario).order_by("inicio"))

    # Convertir episodios a lista de instantes conscientes de zona horaria
    instantes_episodios = []
    for ep in episodios:
        instante = ep.inicio
        if timezone.is_naive(instante):
            instante = timezone.make_aware(instante)
        instantes_episodios.append(instante)

    filas = []
    for idx, reg in enumerate(registros):
        # Punto de observación t = fecha + hora_corte
        hora = reg.hora_corte or time(22, 0)
        dt_corte = timezone.make_aware(datetime.combine(reg.fecha, hora))
        dt_fin_ventana = dt_corte + timedelta(hours=horizonte_horas)

        # Variable objetivo Y: ¿Hubo episodio en [dt_corte, dt_fin_ventana]?
        tuvo_episodio = any(
            dt_corte <= ep_dt <= dt_fin_ventana for ep_dt in instantes_episodios
        )
        target = 1 if tuvo_episodio else 0

        # Factores base del día actual (valores por defecto sensatos si son nulos)
        sueno = float(reg.horas_sueno) if reg.horas_sueno is not None else 7.0
        hidra = MAPA_HIDRATACION.get(reg.hidratacion, 2.0)
        comida = float(reg.comida_omitida) if reg.comida_omitida is not None else 0.0
        estres = float(reg.estres) if reg.estres is not None else 3.0
        pantalla = float(reg.horas_pantalla) if reg.horas_pantalla is not None else 6.0
        actividad = (
            float(reg.minutos_actividad) if reg.minutos_actividad is not None else 30.0
        )
        cafeina = float(reg.cafeina_tazas) if reg.cafeina_tazas is not None else 1.0

        # Historial previo para promedios móviles de 30 días (estrictamente < reg.fecha)
        anteriores_30d = [r for r in registros[:idx] if (reg.fecha - r.fecha).days <= 30]

        if anteriores_30d:
            prom_sueno = np.mean(
                [
                    float(r.horas_sueno)
                    for r in anteriores_30d
                    if r.horas_sueno is not None
                ]
                or [sueno]
            )
            prom_estres = np.mean(
                [float(r.estres) for r in anteriores_30d if r.estres is not None]
                or [estres]
            )
            prom_pantalla = np.mean(
                [
                    float(r.horas_pantalla)
                    for r in anteriores_30d
                    if r.horas_pantalla is not None
                ]
                or [pantalla]
            )
            prom_actividad = np.mean(
                [
                    float(r.minutos_actividad)
                    for r in anteriores_30d
                    if r.minutos_actividad is not None
                ]
                or [actividad]
            )
        else:
            prom_sueno = sueno
            prom_estres = estres
            prom_pantalla = pantalla
            prom_actividad = actividad

        # Deltas respecto a la media de 30 días
        delta_sueno = sueno - prom_sueno
        delta_estres = estres - prom_estres
        delta_pantalla = pantalla - prom_pantalla
        delta_actividad = actividad - prom_actividad

        # Frecuencia de episodios en ventanas previas de 7, 14 y 30 días (previos a dt_corte)
        ep_previos_7d = sum(
            1
            for ep_dt in instantes_episodios
            if dt_corte - timedelta(days=7) <= ep_dt < dt_corte
        )
        ep_previos_14d = sum(
            1
            for ep_dt in instantes_episodios
            if dt_corte - timedelta(days=14) <= ep_dt < dt_corte
        )
        ep_previos_30d = sum(
            1
            for ep_dt in instantes_episodios
            if dt_corte - timedelta(days=30) <= ep_dt < dt_corte
        )

        filas.append(
            {
                "fecha": reg.fecha,
                "dt_corte": dt_corte,
                # Factores base
                "horas_sueno": sueno,
                "hidratacion": hidra,
                "comida_omitida": comida,
                "estres": estres,
                "horas_pantalla": pantalla,
                "minutos_actividad": actividad,
                "cafeina_tazas": cafeina,
                # Promedios 30 días
                "prom_sueno_30d": prom_sueno,
                "prom_estres_30d": prom_estres,
                "prom_pantalla_30d": prom_pantalla,
                "prom_actividad_30d": prom_actividad,
                # Variaciones
                "delta_sueno": delta_sueno,
                "delta_estres": delta_estres,
                "delta_pantalla": delta_pantalla,
                "delta_actividad": delta_actividad,
                # Episodios previos
                "frecuencia_ep_7d": float(ep_previos_7d),
                "frecuencia_ep_14d": float(ep_previos_14d),
                "frecuencia_ep_30d": float(ep_previos_30d),
                # Target
                "target": target,
            }
        )

    df = pd.DataFrame(filas)
    columnas_features = [
        "horas_sueno",
        "hidratacion",
        "comida_omitida",
        "estres",
        "horas_pantalla",
        "minutos_actividad",
        "cafeina_tazas",
        "delta_sueno",
        "delta_estres",
        "delta_pantalla",
        "delta_actividad",
        "frecuencia_ep_7d",
        "frecuencia_ep_14d",
        "frecuencia_ep_30d",
    ]

    X = df[columnas_features]
    y = df["target"]

    return X, y, df
