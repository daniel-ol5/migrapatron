"""
Módulo M3 - Explicabilidad y Reportes.

Presenta los resultados de forma comprensible y genera información resumida
para apoyar una consulta.

Las explicaciones se arman con PLANTILLAS CONTROLADAS: frases fijas con huecos
que el motor rellena. No se genera texto libre. La razón es de calidad, no de
comodidad: una plantilla se puede revisar, versionar y probar, y nunca va a
afirmar algo que los datos no sostienen. Un generador libre sí podría.
"""

from django.db import models
from django.utils import timezone

from apps.m0_usuarios.models import Usuario
from apps.m2_analisis.models import Analisis


class PlantillaExplicacion(models.Model):
    """
    M3.1. Las frases con las que se componen las explicaciones.

    El cuerpo admite marcadores que el explicador sustituye:
    {casos}, {total}, {factores}, {lift}, {periodo}, {confianza}.
    """

    codigo = models.CharField("código", max_length=40, unique=True)
    descripcion = models.CharField("para qué sirve", max_length=150)
    cuerpo = models.TextField(
        "cuerpo con marcadores",
        help_text=(
            "Ej.: 'En {casos} de tus {total} episodios habías {factores} en las "
            "horas previas.'"
        ),
    )
    activa = models.BooleanField("activa", default=True)
    orden = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        db_table = "plantilla_explicacion"
        verbose_name = "plantilla de explicación"
        verbose_name_plural = "plantillas de explicación"
        ordering = ["orden", "codigo"]

    def __str__(self):
        return self.codigo


class ReporteClinico(models.Model):
    """
    M3.3. El resumen imprimible que el paciente lleva a la consulta.

    El contenido se congela al generarlo. Si el paciente registra más datos
    después, se genera un reporte nuevo: el que ya imprimió debe seguir
    coincidiendo con el papel que tiene en la mano.
    """

    class Formato(models.TextChoices):
        PDF = "PDF", "PDF imprimible"
        TEXTO = "TEXTO", "Texto plano"

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="reportes"
    )
    analisis = models.ForeignKey(
        Analisis,
        on_delete=models.PROTECT,
        related_name="reportes",
        help_text="Todo reporte es trazable a la corrida que lo respalda.",
    )

    generado_en = models.DateTimeField("generado en", default=timezone.now)
    periodo_inicio = models.DateField("inicio del periodo")
    periodo_fin = models.DateField("fin del periodo")

    # ------------------------------------------------- contenido congelado
    total_episodios = models.PositiveIntegerField("episodios del periodo")
    intensidad_media = models.DecimalField(
        "intensidad media", max_digits=4, decimal_places=2, null=True, blank=True
    )
    sintomas_frecuentes = models.JSONField(
        "síntomas más frecuentes", default=list, blank=True
    )
    dias_medicacion_rescate = models.PositiveIntegerField(
        "días con medicación de rescate",
        default=0,
        help_text=(
            "Dato clínicamente relevante: un uso frecuente puede indicar "
            "cefalea por abuso de medicación, y es algo que el médico necesita "
            "ver aunque el sistema no lo interprete."
        ),
    )
    patrones = models.JSONField(
        "patrones con su evidencia",
        default=list,
        blank=True,
        help_text="Cada patrón con su explicación, soporte, confianza, lift y casos.",
    )

    deslinde = models.TextField(
        "deslinde médico",
        help_text="M3.2. Se incluye siempre, sin excepción.",
    )

    formato = models.CharField(
        "formato", max_length=6, choices=Formato.choices, default=Formato.PDF
    )
    hash_contenido = models.CharField(
        "hash del contenido",
        max_length=64,
        blank=True,
        default="",
        help_text="Permite verificar que un reporte impreso no fue alterado.",
    )
    veces_compartido = models.PositiveIntegerField("veces compartido", default=0)

    class Meta:
        db_table = "reporte_clinico"
        verbose_name = "reporte clínico"
        verbose_name_plural = "reportes clínicos"
        ordering = ["-generado_en"]
        indexes = [models.Index(fields=["usuario", "-generado_en"])]

    def __str__(self):
        return f"Reporte de {self.usuario.email} · {self.periodo_inicio} a {self.periodo_fin}"
