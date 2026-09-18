"""Rutas de M1 - captura estructurada. Se completan en HU-05, HU-06 y HU-07."""

from django.urls import path

app_name = "bitacora"

urlpatterns = [
    # path("bitacora/", BitacoraListCreate.as_view()),                   # CU-05
    # path("bitacora/<slug:fecha>/", BitacoraDetalle.as_view()),         # CU-05
    # path("bitacora/lote/", SincronizarLote.as_view()),                 # RNF-04
    # path("episodios/", EpisodioListCreate.as_view()),                  # CU-06
    # path("episodios/<int:pk>/", EpisodioDetalle.as_view()),            # CU-06
    # path("catalogos/factores/", CatalogoFactores.as_view()),           # soporte
]
