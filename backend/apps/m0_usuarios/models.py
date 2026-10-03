"""
Módulo M0 - Gestión de Usuarios y Privacidad.

Administra la identidad del usuario, su sesión, el consentimiento y el control
sobre sus datos personales.

La decisión de diseño central de este módulo: el consentimiento NO es un
booleano. Es un historial de hechos. Cada vez que el usuario acepta o retira su
consentimiento se agrega una fila nueva, nunca se sobrescribe la anterior, y
cada fila apunta a la VERSIÓN EXACTA del aviso de privacidad que estaba vigente
en ese momento. Así se puede responder, meses después, a qué texto consintió
esta persona y cuándo. Un booleano no puede responder eso.
"""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class GestorUsuario(BaseUserManager):
    """Crea usuarios y superusuarios usando el email como identificador."""

    use_in_migrations = True

    def _crear(self, email, password, **extra):
        if not email:
            raise ValueError("El email es obligatorio.")
        usuario = self.model(email=self.normalize_email(email).lower(), **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._crear(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if not extra.get("is_staff") or not extra.get("is_superuser"):
            raise ValueError("Un superusuario necesita is_staff e is_superuser.")
        return self._crear(email, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """HU-01, HU-02. El paciente se identifica por email, no por username."""

    class Sexo(models.TextChoices):
        FEMENINO = "F", "Femenino"
        MASCULINO = "M", "Masculino"
        OTRO = "OTRO", "Otro"
        NO_DECLARA = "NS", "Prefiere no decirlo"

    email = models.EmailField("email", max_length=150, unique=True)
    nombre = models.CharField("nombre", max_length=80)
    apellido = models.CharField("apellido", max_length=80)
    fecha_nacimiento = models.DateField("fecha de nacimiento", null=True, blank=True)
    sexo = models.CharField(
        "sexo", max_length=4, choices=Sexo.choices, blank=True, default=""
    )
    zona_horaria = models.CharField(
        "zona horaria", max_length=40, default="America/La_Paz"
    )

    fecha_registro = models.DateTimeField("fecha de registro", default=timezone.now)
    ultimo_acceso = models.DateTimeField("último acceso", null=True, blank=True)

    is_active = models.BooleanField("activo", default=True)
    is_staff = models.BooleanField("es staff", default=False)

    objects = GestorUsuario()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "apellido"]

    class Meta:
        db_table = "usuario"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return self.email

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}".strip()

    # ---------------------------------------------------------- consentimiento
    @property
    def consentimiento_vigente(self):
        """
        El último hecho de consentimiento, o None si nunca hubo ninguno.

        Se consulta el historial en vez de guardar una bandera, para que no
        puedan quedar desincronizados.
        """
        return self.consentimientos.order_by("-otorgado_en").first()

    @property
    def consintio_analisis(self):
        """True si el último hecho del historial fue una aceptación."""
        ultimo = self.consentimiento_vigente
        return bool(ultimo and ultimo.aceptado)


class PerfilClinico(models.Model):
    """HU-01, HU-04. Contexto clínico del paciente."""

    class TipoMigrana(models.TextChoices):
        CON_AURA = "CON_AURA", "Con aura"
        SIN_AURA = "SIN_AURA", "Sin aura"
        CRONICA = "CRONICA", "Crónica"
        DESCONOCIDA = "DESCONOCIDA", "Desconocida"

    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name="perfil"
    )
    anios_con_migrana = models.PositiveSmallIntegerField(
        "años con migraña", null=True, blank=True
    )
    diagnostico_previo = models.BooleanField("diagnóstico previo", default=False)
    tipo_migrana = models.CharField(
        "tipo de migraña",
        max_length=12,
        choices=TipoMigrana.choices,
        default=TipoMigrana.DESCONOCIDA,
    )
    medicacion_habitual = models.TextField("medicación habitual", blank=True, default="")
    registra_ciclo_menstrual = models.BooleanField(
        "registra contexto menstrual", default=False
    )
    hora_corte_preferida = models.TimeField(
        "hora de corte preferida",
        default="22:00",
        help_text=(
            "Hora a la que el paciente cierra su bitácora del día. M2 la usa "
            "para vincular los factores con los episodios posteriores."
        ),
    )

    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        db_table = "perfil_clinico"
        verbose_name = "perfil clínico"
        verbose_name_plural = "perfiles clínicos"

    def __str__(self):
        return f"Perfil de {self.usuario.email}"


class AvisoPrivacidad(models.Model):
    """
    Versiones del aviso de privacidad.

    Cada consentimiento apunta a la versión que el usuario leyó. El texto de una
    versión publicada no se modifica nunca: si cambia la política, se publica
    una versión nueva. De otro modo el consentimiento guardado dejaría de
    corresponder a lo que la persona realmente aceptó.
    """

    version = models.CharField("versión", max_length=20, unique=True)
    titulo = models.CharField("título", max_length=150)
    contenido = models.TextField("contenido")
    vigente_desde = models.DateTimeField("vigente desde", default=timezone.now)
    es_actual = models.BooleanField("es la versión actual", default=False)

    class Meta:
        db_table = "aviso_privacidad"
        verbose_name = "aviso de privacidad"
        verbose_name_plural = "avisos de privacidad"
        ordering = ["-vigente_desde"]

    def __str__(self):
        return f"Aviso {self.version}"

    def save(self, *args, **kwargs):
        """Marcar una versión como actual desmarca las demás."""
        super().save(*args, **kwargs)
        if self.es_actual:
            AvisoPrivacidad.objects.exclude(pk=self.pk).filter(es_actual=True).update(
                es_actual=False
            )

    @classmethod
    def actual(cls):
        """La versión que se le muestra a quien se está registrando."""
        return cls.objects.filter(es_actual=True).first()


class Consentimiento(models.Model):
    """
    HU-01, HU-04. Un hecho de consentimiento: aceptado o retirado.

    Tabla de solo adición. Para retirar el consentimiento se inserta una fila
    con aceptado=False, no se borra ni se modifica la anterior.
    """

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="consentimientos"
    )
    aviso = models.ForeignKey(
        AvisoPrivacidad, on_delete=models.PROTECT, related_name="consentimientos"
    )
    aceptado = models.BooleanField("aceptado")
    otorgado_en = models.DateTimeField("otorgado en", default=timezone.now)
    ip = models.GenericIPAddressField("IP de origen", null=True, blank=True)

    class Meta:
        db_table = "consentimiento"
        verbose_name = "consentimiento"
        verbose_name_plural = "consentimientos"
        ordering = ["-otorgado_en"]
        indexes = [models.Index(fields=["usuario", "-otorgado_en"])]

    def __str__(self):
        verbo = "aceptó" if self.aceptado else "retiró"
        return f"{self.usuario.email} {verbo} el aviso {self.aviso.version}"


class EventoAuditoria(models.Model):
    """
    Rastro de las operaciones sobre datos clínicos.

    Tabla de solo inserción: nunca se actualiza ni se borra. Un asiento
    sobrevive al dato que describe, para que un borrado también quede
    registrado.
    """

    class Accion(models.TextChoices):
        REGISTRO = "REGISTRO", "Registro de cuenta"
        ACCESO = "ACCESO", "Inicio de sesión"
        ACCESO_FALLIDO = "ACCESO_FALLIDO", "Intento de acceso fallido"
        CIERRE = "CIERRE", "Cierre de sesión"
        CONSENTIMIENTO = "CONSENTIMIENTO", "Cambio de consentimiento"
        CREACION = "CREACION", "Creación de registro"
        EDICION = "EDICION", "Edición de registro"
        ELIMINACION = "ELIMINACION", "Eliminación de registro"
        BAJA_CUENTA = "BAJA_CUENTA", "Eliminación de cuenta"
        ANALISIS = "ANALISIS", "Ejecución de análisis"

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos",
    )
    # Se conserva el email aparte: si la cuenta se elimina, el asiento sigue
    # diciendo de quién fue la operación.
    email_actor = models.EmailField("email del actor", max_length=150, blank=True)
    accion = models.CharField("acción", max_length=20, choices=Accion.choices)
    entidad = models.CharField("entidad", max_length=40, blank=True, default="")
    entidad_id = models.BigIntegerField("id de la entidad", null=True, blank=True)
    detalle = models.JSONField("detalle", default=dict, blank=True)
    ip = models.GenericIPAddressField("IP de origen", null=True, blank=True)
    ocurrido_en = models.DateTimeField("ocurrido en", default=timezone.now)

    class Meta:
        db_table = "evento_auditoria"
        verbose_name = "evento de auditoría"
        verbose_name_plural = "eventos de auditoría"
        ordering = ["-ocurrido_en"]
        indexes = [
            models.Index(fields=["usuario", "-ocurrido_en"]),
            models.Index(fields=["accion", "-ocurrido_en"]),
        ]

    def __str__(self):
        return f"{self.accion} · {self.email_actor} · {self.ocurrido_en:%Y-%m-%d %H:%M}"
