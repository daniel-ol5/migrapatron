"""Rutas raíz de MigraPatrón IA."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Módulo M0 - acceso y perfil
    path("api/auth/", include("apps.cuentas.urls")),
    # Módulo M1 - captura estructurada
    path("api/", include("apps.bitacora.urls")),
    # Módulos M2 y M3 - análisis, hallazgos y reporte
    path("api/", include("apps.analisis.urls")),
    # Documentación
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
