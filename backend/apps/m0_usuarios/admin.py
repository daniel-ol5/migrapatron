from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AvisoPrivacidad,
    Consentimiento,
    EventoAuditoria,
    PerfilClinico,
    Usuario,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ["-fecha_registro"]
    list_display = ["email", "nombre", "apellido", "is_active", "fecha_registro"]
    list_filter = ["is_active", "is_staff", "sexo"]
    search_fields = ["email", "nombre", "apellido"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Datos personales",
            {
                "fields": (
                    "nombre",
                    "apellido",
                    "fecha_nacimiento",
                    "sexo",
                    "zona_horaria",
                )
            },
        ),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Fechas", {"fields": ("fecha_registro", "ultimo_acceso", "last_login")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nombre", "apellido", "password1", "password2"),
            },
        ),
    )
    readonly_fields = ["fecha_registro", "ultimo_acceso", "last_login"]


@admin.register(PerfilClinico)
class PerfilClinicoAdmin(admin.ModelAdmin):
    list_display = [
        "usuario",
        "tipo_migrana",
        "anios_con_migrana",
        "hora_corte_preferida",
    ]
    list_filter = ["tipo_migrana", "diagnostico_previo", "registra_ciclo_menstrual"]
    search_fields = ["usuario__email"]


@admin.register(AvisoPrivacidad)
class AvisoPrivacidadAdmin(admin.ModelAdmin):
    list_display = ["version", "titulo", "es_actual", "vigente_desde"]
    list_filter = ["es_actual"]


@admin.register(Consentimiento)
class ConsentimientoAdmin(admin.ModelAdmin):
    list_display = ["usuario", "aceptado", "aviso", "otorgado_en"]
    list_filter = ["aceptado", "aviso"]
    search_fields = ["usuario__email"]

    # Historial de solo adicion: no se edita ni se borra desde el admin.
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EventoAuditoria)
class EventoAuditoriaAdmin(admin.ModelAdmin):
    list_display = ["ocurrido_en", "accion", "email_actor", "entidad", "entidad_id"]
    list_filter = ["accion", "entidad"]
    search_fields = ["email_actor", "entidad"]
    readonly_fields = [f.name for f in EventoAuditoria._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
