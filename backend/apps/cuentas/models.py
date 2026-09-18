"""
Módulo M0 - identidad y perfil clínico.

El paciente se identifica por email, no por username. Por eso se define un
modelo de usuario propio: cambiarlo después de la primera migración es muy
costoso, así que va desde el día uno (HU-01).
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
        email = self.normalize_email(email).lower()
        usuario = self.model(email=email, **extra)
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
        if extra.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")
        return self._crear(email, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
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


class PerfilClinico(models.Model):
    """
    Contexto clínico del paciente y su consentimiento para el análisis.

    RN-01: sin `consentimiento_analisis` en True, CU-08 no se ejecuta.
    """

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
    ciclo_menstrual_aplica = models.BooleanField(
        "registra ciclo menstrual", default=False
    )

    consentimiento_analisis = models.BooleanField(
        "consintió el análisis de sus datos", default=False
    )
    fecha_consentimiento = models.DateTimeField(
        "fecha del consentimiento", null=True, blank=True
    )

    class Meta:
        db_table = "perfil_clinico"
        verbose_name = "perfil clínico"
        verbose_name_plural = "perfiles clínicos"

    def __str__(self):
        return f"Perfil de {self.usuario.email}"

    def otorgar_consentimiento(self):
        """Acepta el análisis y sella la fecha. Idempotente."""
        if not self.consentimiento_analisis:
            self.consentimiento_analisis = True
            self.fecha_consentimiento = timezone.now()
            self.save(
                update_fields=["consentimiento_analisis", "fecha_consentimiento"]
            )

    def revocar_consentimiento(self):
        self.consentimiento_analisis = False
        self.fecha_consentimiento = None
        self.save(update_fields=["consentimiento_analisis", "fecha_consentimiento"])
