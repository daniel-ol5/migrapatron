"""Rutas de M1 - Seguimiento y Bitacora Diaria."""

from django.urls import path

from . import views

app_name = "m1_bitacora"

urlpatterns = [
    # M1.1 Registro diario
    path(
        "bitacora/",
        views.RegistroDiarioListCreateView.as_view(),
        name="bitacora-lista",
    ),  # HU-05
    path(
        "bitacora/fecha/<slug:fecha>/",
        views.RegistroDiarioPorFechaView.as_view(),
        name="bitacora-por-fecha",
    ),
    path(
        "bitacora/<int:pk>/",
        views.RegistroDiarioDetalleView.as_view(),
        name="bitacora-detalle",
    ),  # HU-08, HU-09
    # M1.2 Registro de episodios
    path(
        "episodios/",
        views.EpisodioListCreateView.as_view(),
        name="episodio-lista",
    ),  # HU-06
    path(
        "episodios/<int:pk>/",
        views.EpisodioDetalleView.as_view(),
        name="episodio-detalle",
    ),  # HU-08, HU-09
    # M1.3 Consulta del historial propio
    path("historial/", views.HistorialView.as_view(), name="historial"),  # HU-07
]
