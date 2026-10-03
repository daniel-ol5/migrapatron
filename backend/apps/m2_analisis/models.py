"""
Módulo M2 - Análisis Inteligente de Datos.

Prepara los registros personales y obtiene asociaciones cuando la evidencia
alcanza los criterios mínimos establecidos.

Los umbrales del documento viven en settings.MOTOR, no incrustados aquí, y cada
corrida guarda los que usó en `parametros`. Así una corrida vieja sigue siendo
interpretable después de que el equipo ajuste un umbral.

Sobre el ajuste de Benjamini-Hochberg: al probar doce factores a la vez contra
los episodios, con un umbral de p < 0,05 se espera un falso positivo cada veinte
pruebas por puro azar. BH corrige esa inflación controlando la tasa de falsos
descubrimientos. Es la diferencia entre presentar un patrón real y presentar
ruido con apariencia de patrón, y en un sistema de salud eso importa.
"""

from django.db import models
from django.utils import timezone

from apps.m0_usuarios.models import Usuario


class Analisis(models.Model):
    """Una corrida del motor. Inmutable una vez terminada."""

    class Estado(models.TextChoices):
        OK = "OK", "Completado"
        DATOS_INSUFICIENTES = "DATOS_INSUFICIENTES", "Datos insuficientes"
        ERROR = "ERROR", "Error durante el análisis"

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="analisis"
    )
    ejecutado_en = models.DateTimeField("ejecutado en", default=timezone.now)

    periodo_inicio = models.DateField("inicio del periodo")
    periodo_fin = models.DateField("fin del periodo")

    bitacoras_analizadas = models.PositiveIntegerField("bitácoras analizadas")
    episodios_analizados = models.PositiveIntegerField("episodios analizados")
    episodios_vinculados = models.PositiveIntegerField(
        "episodios vinculados",
        default=0,
        help_text="Episodios que quedaron dentro de la ventana temporal.",
    )

    ventana_horas = models.PositiveSmallIntegerField(
        "ventana temporal en horas",
        default=48,
        help_text="Cuánto hacia atrás se buscan factores previos al episodio.",
    )

    version_motor = models.CharField("versión del motor", max_length=20)
    parametros = models.JSONField(
        "parámetros usados",
        default=dict,
        help_text="Umbrales de soporte, confianza, lift, casos mínimos y alfa.",
    )

    estado = models.CharField("estado", max_length=20, choices=Estado.choices)
    mensaje_estado = models.CharField(
        "mensaje del estado", max_length=250, blank=True, default=""
    )
    duracion_ms = models.PositiveIntegerField(
        "duración en milisegundos", null=True, blank=True
    )

    class Meta:
        db_table = "analisis"
        verbose_name = "análisis"
        verbose_name_plural = "análisis"
        ordering = ["-ejecutado_en"]
        indexes = [models.Index(fields=["usuario", "-ejecutado_en"])]

    def __str__(self):
        return (
            f"{self.usuario.email} · {self.ejecutado_en:%Y-%m-%d %H:%M} · {self.estado}"
        )

    @property
    def tiene_hallazgos(self):
        return self.estado == self.Estado.OK and self.hallazgos.exists()


class Hallazgo(models.Model):
    """
    Un patrón encontrado, con toda su evidencia estadística.

    Cuelga de `analisis` y no del usuario a propósito: un hallazgo solo
    significa algo dentro del contexto de su corrida (periodo, umbrales,
    versión del motor). Los hallazgos no se editan nunca, se regeneran.
    """

    class Tipo(models.TextChoices):
        ASOCIACION = "ASOCIACION", "Regla de asociación (Apriori)"
        FRECUENCIA = "FRECUENCIA", "Frecuencia de aparición"

    class NivelConfianza(models.TextChoices):
        ALTA = "ALTA", "Alta"
        MEDIA = "MEDIA", "Media"
        BAJA = "BAJA", "Baja"

    analisis = models.ForeignKey(
        Analisis, on_delete=models.CASCADE, related_name="hallazgos"
    )
    tipo = models.CharField(
        "tipo", max_length=12, choices=Tipo.choices, default=Tipo.ASOCIACION
    )

    antecedente = models.JSONField(
        "antecedente",
        default=list,
        help_text='Ítems del patrón, p. ej. ["SUENO_BAJO", "COMIDA_OMITIDA"].',
    )

    # ------------------------------------------------- evidencia
    soporte = models.DecimalField("soporte", max_digits=6, decimal_places=4)
    confianza = models.DecimalField("confianza", max_digits=6, decimal_places=4)
    lift = models.DecimalField("lift", max_digits=7, decimal_places=3)
    casos = models.PositiveIntegerField(
        "casos", help_text="Episodios en los que el patrón estuvo presente."
    )
    total_episodios = models.PositiveIntegerField("total de episodios del periodo")

    p_valor = models.DecimalField(
        "p-valor (Fisher exacto)",
        max_digits=8,
        decimal_places=6,
        null=True,
        blank=True,
    )
    p_ajustado = models.DecimalField(
        "p-valor ajustado (Benjamini-Hochberg)",
        max_digits=8,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Controla la tasa de falsos descubrimientos al probar varios factores.",
    )
    significativo = models.BooleanField(
        "significativo tras el ajuste",
        default=False,
        help_text="True si p_ajustado quedó por debajo del alfa configurado.",
    )

    nivel_confianza = models.CharField(
        "nivel de confianza", max_length=5, choices=NivelConfianza.choices
    )
    ranking = models.PositiveSmallIntegerField("posición en el ranking")

    class Meta:
        db_table = "hallazgo"
        verbose_name = "hallazgo"
        verbose_name_plural = "hallazgos"
        ordering = ["analisis", "ranking"]
        indexes = [models.Index(fields=["analisis", "ranking"])]

    def __str__(self):
        return f"#{self.ranking} {self.antecedente} (lift {self.lift})"


class Explicacion(models.Model):
    """
    M3.1. El texto en lenguaje natural de un hallazgo.

    Se guarda junto con la plantilla que lo generó. Si la redacción de una
    plantilla cambia, las explicaciones ya emitidas siguen diciendo lo que el
    paciente leyó, que es lo que importa cuando lleva el resumen a consulta.
    """

    hallazgo = models.OneToOneField(
        Hallazgo, on_delete=models.CASCADE, related_name="explicacion"
    )
    plantilla_codigo = models.CharField("código de la plantilla", max_length=40)
    texto = models.TextField("texto de la explicación")
    generada_en = models.DateTimeField("generada en", default=timezone.now)

    class Meta:
        db_table = "explicacion"
        verbose_name = "explicación"
        verbose_name_plural = "explicaciones"

    def __str__(self):
        return self.texto[:70]


class ValoracionHallazgo(models.Model):
    """El paciente marca si un hallazgo le resultó útil."""

    hallazgo = models.ForeignKey(
        Hallazgo, on_delete=models.CASCADE, related_name="valoraciones"
    )
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="valoraciones"
    )
    util = models.BooleanField("le resultó útil")
    comentario = models.CharField("comentario", max_length=300, blank=True, default="")
    creado_en = models.DateTimeField("creado en", default=timezone.now)

    class Meta:
        db_table = "valoracion_hallazgo"
        verbose_name = "valoración de hallazgo"
        verbose_name_plural = "valoraciones de hallazgos"
        constraints = [
            models.UniqueConstraint(
                fields=["hallazgo", "usuario"], name="una_valoracion_por_hallazgo"
            )
        ]

    def __str__(self):
        veredicto = "util" if self.util else "no util"
        return f"{self.usuario.email}: {veredicto}"
