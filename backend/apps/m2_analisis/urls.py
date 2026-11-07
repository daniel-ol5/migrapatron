"""Rutas de M2 - Análisis Inteligente y Predicción Personal Supervisada."""

from django.urls import path

from . import views

app_name = "m2_analisis"

urlpatterns = [
    # M2.1 / M2.2 / M2.3: Ejecutar análisis supervisado L2 y estimación
    path("analisis/", views.EjecutarAnalisisView.as_view(), name="analisis-ejecutar"),
    # CU-10 / HU-11: Última estimación
    path("analisis/ultimo/", views.UltimoAnalisisView.as_view(), name="analisis-ultimo"),
    # RF-07A: Estado de suficiencia y avance (barra 60 días)
    path(
        "analisis/suficiencia/",
        views.EstadoSuficienciaView.as_view(),
        name="analisis-suficiencia",
    ),
    # HU-18 / RF-15: Conteo de medicación de rescate en 30 días
    path(
        "analisis/medicacion/",
        views.AlertaMedicacionView.as_view(),
        name="analisis-medicacion",
    ),
]
