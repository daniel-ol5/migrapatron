"""Rutas raiz de MigraPatron IA."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # M0 - Gestion de Usuarios y Privacidad
    path("api/auth/", include("apps.m0_usuarios.urls")),
    # M1 - Seguimiento y Bitacora Diaria
    path("api/", include("apps.m1_bitacora.urls")),
    # M2 - Analisis Inteligente de Datos
    path("api/", include("apps.m2_analisis.urls")),
    # M3 - Explicabilidad y Reportes
    path("api/", include("apps.m3_reportes.urls")),
    # Documentacion
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
