from django.contrib import admin

from .models import Episodio, RegistroDiario


@admin.register(RegistroDiario)
class RegistroDiarioAdmin(admin.ModelAdmin):
    list_display = ["usuario", "fecha", "hora_corte", "completado", "medicacion_rescate"]
    list_filter = ["completado", "medicacion_rescate", "hidratacion"]
    search_fields = ["usuario__email"]
    date_hierarchy = "fecha"


@admin.register(Episodio)
class EpisodioAdmin(admin.ModelAdmin):
    list_display = ["usuario", "inicio", "intensidad", "duracion_min", "registro_diario"]
    list_filter = ["intensidad", "nauseas", "vomitos", "sensibilidad_luz"]
    search_fields = ["usuario__email"]
    date_hierarchy = "inicio"
