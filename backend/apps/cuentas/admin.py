from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PerfilClinico, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ["-fecha_registro"]
    list_display = ["email", "nombre", "apellido", "is_active", "fecha_registro"]
    list_filter = ["is_active", "is_staff", "sexo"]
    search_fields = ["email", "nombre", "apellido"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos personales", {
            "fields": ("nombre", "apellido", "fecha_nacimiento", "sexo", "zona_horaria")
        }),
        ("Permisos", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Fechas", {"fields": ("fecha_registro", "ultimo_acceso", "last_login")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "nombre", "apellido", "password1", "password2"),
        }),
    )
    readonly_fields = ["fecha_registro", "ultimo_acceso", "last_login"]


@admin.register(PerfilClinico)
class PerfilClinicoAdmin(admin.ModelAdmin):
    list_display = [
        "usuario",
        "tipo_migrana",
        "anios_con_migrana",
        "consentimiento_analisis",
        "fecha_consentimiento",
    ]
    list_filter = ["consentimiento_analisis", "tipo_migrana", "diagnostico_previo"]
    search_fields = ["usuario__email"]
    readonly_fields = ["fecha_consentimiento"]
