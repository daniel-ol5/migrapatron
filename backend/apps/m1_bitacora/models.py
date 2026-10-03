"""
Módulo M1 - Seguimiento y Bitácora Diaria.

Conserva de forma estructurada los hábitos cotidianos y los episodios
informados por cada usuario.

Dos decisiones de diseño que vale la pena justificar:

1. HORA DE CORTE. Cada bitácora guarda la hora a la que el paciente la cerró.
   M2 la necesita para vincular: un episodio que empieza a las 3 de la mañana
   se relaciona con la bitácora del día anterior, no con la del día en curso.
   Sin la hora de corte, la ventana de 48 horas no se puede calcular bien.

2. SÍNTOMAS COMO COLUMNAS, NO COMO CATÁLOGO. Náuseas, vómitos y las dos
   sensibilidades son campos del episodio. Son los cuatro síntomas que el
   documento fija, no una lista que crezca, así que una tabla N:M solo añadiría
   consultas sin ganar nada. Validar un booleano es trivial; validar una
   relación no lo es.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.m0_usuarios.models import Usuario


class RegistroDiario(models.Model):
    """
    HU-05. Un día de bitácora.

    Unicidad (usuario, fecha): un paciente tiene como máximo un registro por
    día. Si vuelve a la pantalla, edita el que ya existe en vez de crear otro.
    """

    class Hidratacion(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"

    class ContextoMenstrual(models.TextChoices):
        NO_APLICA = "NO_APLICA", "No aplica"
        MENSTRUACION = "MENSTRUACION", "Menstruación"
        FOLICULAR = "FOLICULAR", "Fase folicular"
        OVULACION = "OVULACION", "Ovulación"
        LUTEA = "LUTEA", "Fase lútea"

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="registros"
    )
    fecha = models.DateField("fecha")
    hora_corte = models.TimeField(
        "hora de corte",
        help_text="Hora a la que se cerró la bitácora de este día.",
    )

    # ------------------------------------------------- factores cotidianos
    horas_sueno = models.DecimalField(
        "horas de sueño",
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )
    hidratacion = models.CharField(
        "hidratación",
        max_length=5,
        choices=Hidratacion.choices,
        blank=True,
        default="",
    )
    comida_omitida = models.PositiveSmallIntegerField(
        "comidas omitidas",
        null=True,
        blank=True,
        validators=[MaxValueValidator(3)],
    )
    estres = models.PositiveSmallIntegerField(
        "estrés percibido",
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    horas_pantalla = models.DecimalField(
        "horas frente a pantallas",
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )
    minutos_actividad = models.PositiveSmallIntegerField(
        "minutos de actividad física",
        null=True,
        blank=True,
        validators=[MaxValueValidator(1440)],
    )
    cafeina_tazas = models.PositiveSmallIntegerField(
        "tazas de cafeína",
        null=True,
        blank=True,
        validators=[MaxValueValidator(20)],
    )

    # ------------------------------------------------- contexto clínico
    contexto_menstrual = models.CharField(
        "contexto menstrual",
        max_length=12,
        choices=ContextoMenstrual.choices,
        blank=True,
        default="",
        help_text="Opcional. Solo si el paciente eligió registrarlo.",
    )
    medicacion_rescate = models.BooleanField("tomó medicación de rescate", default=False)
    sensaciones_premonitorias = models.BooleanField(
        "tuvo sensaciones premonitorias",
        default=False,
        help_text="Bostezos, antojos, irritabilidad, rigidez de cuello.",
    )

    # ------------------------------------------------- metadatos
    completado = models.BooleanField(
        "completado",
        default=False,
        help_text="Solo los días completos cuentan para el análisis de M2.",
    )
    creado_en = models.DateTimeField("creado en", default=timezone.now)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    # Los factores que M2 exige para considerar el día utilizable.
    FACTORES_REQUERIDOS = (
        "horas_sueno",
        "hidratacion",
        "comida_omitida",
        "estres",
        "horas_pantalla",
        "minutos_actividad",
        "cafeina_tazas",
    )

    class Meta:
        db_table = "registro_diario"
        verbose_name = "registro diario"
        verbose_name_plural = "registros diarios"
        ordering = ["-fecha"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "fecha"], name="un_registro_por_usuario_y_fecha"
            )
        ]
        indexes = [models.Index(fields=["usuario", "-fecha"])]

    def __str__(self):
        return f"{self.usuario.email} · {self.fecha}"

    def save(self, *args, **kwargs):
        self.completado = self.calcular_completado()
        super().save(*args, **kwargs)

    def calcular_completado(self):
        """
        Un día está completo cuando ningún factor requerido quedó vacío.

        Los campos opcionales por diseño (contexto menstrual) no se cuentan:
        exigirlos dejaría incompletos todos los días de quien no lo registra.
        """
        return all(
            self._tiene_valor(getattr(self, campo)) for campo in self.FACTORES_REQUERIDOS
        )

    @staticmethod
    def _tiene_valor(valor):
        return valor is not None and valor != ""


class Episodio(models.Model):
    """
    HU-06. Un episodio de migraña.

    La intensidad usa la escala EVA de 1 a 10. Los cuatro síntomas acompañantes
    son los que fija el documento de M1.
    """

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="episodios"
    )
    registro_diario = models.ForeignKey(
        RegistroDiario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="episodios",
        help_text=(
            "Bitácora del día en que empezó, si existe. Se pone en nulo al "
            "borrar la bitácora: el episodio es el dato clínico valioso y se "
            "conserva aunque pierda su contexto diario."
        ),
    )

    inicio = models.DateTimeField("inicio")
    duracion_min = models.PositiveIntegerField(
        "duración en minutos",
        null=True,
        blank=True,
        validators=[MaxValueValidator(10080)],  # 7 días
        help_text="Nulo mientras el episodio sigue en curso.",
    )
    intensidad = models.PositiveSmallIntegerField(
        "intensidad (EVA 1-10)",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    # ------------------------------------------------- síntomas acompañantes
    nauseas = models.BooleanField("náuseas", default=False)
    vomitos = models.BooleanField("vómitos", default=False)
    sensibilidad_luz = models.BooleanField("sensibilidad a la luz", default=False)
    sensibilidad_sonido = models.BooleanField("sensibilidad al sonido", default=False)

    observacion = models.TextField("observación", blank=True, default="")

    creado_en = models.DateTimeField("creado en", default=timezone.now)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        db_table = "episodio"
        verbose_name = "episodio"
        verbose_name_plural = "episodios"
        ordering = ["-inicio"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(intensidad__gte=1, intensidad__lte=10),
                name="intensidad_entre_1_y_10",
            )
        ]
        indexes = [models.Index(fields=["usuario", "-inicio"])]

    def __str__(self):
        return (
            f"{self.usuario.email} · {self.inicio:%Y-%m-%d %H:%M} · EVA {self.intensidad}"
        )

    @property
    def en_curso(self):
        return self.duracion_min is None

    @property
    def fin_estimado(self):
        if self.duracion_min is None:
            return None
        return self.inicio + timezone.timedelta(minutes=self.duracion_min)

    @property
    def sintomas_presentes(self):
        """Lista legible, para las explicaciones de M3 y el resumen clínico."""
        mapa = (
            (self.nauseas, "náuseas"),
            (self.vomitos, "vómitos"),
            (self.sensibilidad_luz, "sensibilidad a la luz"),
            (self.sensibilidad_sonido, "sensibilidad al sonido"),
        )
        return [nombre for presente, nombre in mapa if presente]

    def vincular_bitacora(self):
        """
        Ancla el episodio a la bitácora que lo precede según la hora de corte.

        Si el episodio empezó ANTES de la hora de corte de su propio día, le
        corresponde la bitácora de ese día. Si empezó después, esa bitácora ya
        estaba cerrada, así que se vincula igual al día en que ocurrió — la
        ventana temporal de M2 es la que decide qué factores se consideran
        previos.
        """
        fecha = timezone.localtime(self.inicio).date()
        self.registro_diario = RegistroDiario.objects.filter(
            usuario=self.usuario, fecha=fecha
        ).first()
        return self.registro_diario
