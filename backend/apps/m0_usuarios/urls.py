"""Rutas de M0 - Gestion de Usuarios y Privacidad."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "m0_usuarios"

urlpatterns = [
    # M0.1 Registro con aceptacion del aviso de privacidad
    path("aviso-privacidad/", views.AvisoPrivacidadActualView.as_view(), name="aviso"),
    path("registro/", views.RegistroView.as_view(), name="registro"),  # HU-01
    # M0.2 Inicio y cierre seguro de sesion
    path("login/", views.LoginView.as_view(), name="login"),  # HU-02
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),  # HU-03
    # M0.3 Consulta y actualizacion del perfil propio
    path("perfil/", views.PerfilView.as_view(), name="perfil"),  # HU-04
    path("consentimiento/", views.ConsentimientoView.as_view(), name="consentimiento"),
    # M0.4 Eliminacion de la cuenta y de los datos personales
    path("baja/", views.BajaCuentaView.as_view(), name="baja"),
]
