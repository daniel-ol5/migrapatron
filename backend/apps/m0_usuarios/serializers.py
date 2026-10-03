"""Serializadores de M0 - Gestión de Usuarios y Privacidad."""

from django.contrib.auth import authenticate, password_validation
from django.db import transaction
from rest_framework import serializers

from .models import AvisoPrivacidad, Consentimiento, PerfilClinico, Usuario


class AvisoPrivacidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvisoPrivacidad
        fields = ["version", "titulo", "contenido", "vigente_desde"]


class PerfilClinicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilClinico
        fields = [
            "anios_con_migrana",
            "diagnostico_previo",
            "tipo_migrana",
            "medicacion_habitual",
            "registra_ciclo_menstrual",
            "hora_corte_preferida",
            "actualizado_en",
        ]
        read_only_fields = ["actualizado_en"]


class ConsentimientoSerializer(serializers.ModelSerializer):
    """HU-04. Solo lectura: el historial se consulta, no se edita."""

    aviso_version = serializers.CharField(source="aviso.version", read_only=True)

    class Meta:
        model = Consentimiento
        fields = ["id", "aceptado", "aviso_version", "otorgado_en"]
        read_only_fields = fields


class UsuarioSerializer(serializers.ModelSerializer):
    """Vista del usuario que devuelven el login y el perfil."""

    perfil = PerfilClinicoSerializer(read_only=True)
    consintio_analisis = serializers.BooleanField(read_only=True)
    nombre_completo = serializers.CharField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "email",
            "nombre",
            "apellido",
            "nombre_completo",
            "fecha_nacimiento",
            "sexo",
            "zona_horaria",
            "fecha_registro",
            "consintio_analisis",
            "perfil",
        ]
        read_only_fields = ["id", "email", "fecha_registro"]


class RegistroSerializer(serializers.Serializer):
    """
    HU-01. Registro con aceptación del aviso de privacidad.

    Exige la versión del aviso que el usuario tenía en pantalla. Si mientras
    llenaba el formulario se publicó una versión nueva, el registro se rechaza
    y debe leer la vigente: aceptar un texto que ya no rige no es consentir.
    """

    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    nombre = serializers.CharField(max_length=80)
    apellido = serializers.CharField(max_length=80)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    sexo = serializers.ChoiceField(
        choices=Usuario.Sexo.choices, required=False, allow_blank=True, default=""
    )

    acepta_aviso = serializers.BooleanField()
    version_aviso = serializers.CharField(max_length=20)

    def validate_email(self, valor):
        valor = valor.lower().strip()
        if Usuario.objects.filter(email=valor).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este email.")
        return valor

    def validate_password(self, valor):
        password_validation.validate_password(valor)
        return valor

    def validate_acepta_aviso(self, valor):
        if not valor:
            raise serializers.ValidationError(
                "Hay que aceptar el aviso de privacidad para crear la cuenta."
            )
        return valor

    def validate_version_aviso(self, valor):
        aviso = AvisoPrivacidad.objects.filter(version=valor).first()
        if aviso is None:
            raise serializers.ValidationError("La versión del aviso no existe.")
        if not aviso.es_actual:
            raise serializers.ValidationError(
                "El aviso de privacidad cambió. Vuelve a leerlo antes de continuar."
            )
        self._aviso = aviso
        return valor

    @transaction.atomic
    def create(self, datos):
        datos.pop("acepta_aviso")
        datos.pop("version_aviso")
        password = datos.pop("password")

        usuario = Usuario.objects.create_user(password=password, **datos)
        PerfilClinico.objects.create(usuario=usuario)
        Consentimiento.objects.create(
            usuario=usuario,
            aviso=self._aviso,
            aceptado=True,
            ip=self.context.get("ip"),
        )
        return usuario


class LoginSerializer(serializers.Serializer):
    """
    HU-02. Inicio de sesión mediante autenticación de Django.

    El mensaje de error es idéntico para email inexistente y contraseña
    incorrecta. Distinguirlos permitiría averiguar qué emails tienen cuenta en
    una aplicación de salud, y eso ya es filtrar información sensible.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    ERROR = "Email o contraseña incorrectos."

    def validate(self, datos):
        usuario = authenticate(
            request=self.context.get("request"),
            username=datos["email"].lower().strip(),
            password=datos["password"],
        )
        if usuario is None:
            raise serializers.ValidationError({"detail": self.ERROR})
        if not usuario.is_active:
            raise serializers.ValidationError({"detail": "La cuenta está desactivada."})

        datos["usuario"] = usuario
        return datos


class CambioConsentimientoSerializer(serializers.Serializer):
    """HU-04. Otorgar o retirar el consentimiento."""

    aceptado = serializers.BooleanField()
    version_aviso = serializers.CharField(max_length=20, required=False)

    def validate(self, datos):
        if datos["aceptado"]:
            version = datos.get("version_aviso")
            aviso = (
                AvisoPrivacidad.objects.filter(version=version).first()
                if version
                else AvisoPrivacidad.actual()
            )
            if aviso is None:
                raise serializers.ValidationError(
                    {"version_aviso": "La versión del aviso no existe."}
                )
            if not aviso.es_actual:
                raise serializers.ValidationError(
                    {"version_aviso": "Solo se puede aceptar la versión vigente."}
                )
        else:
            # Para retirarlo se asienta contra el mismo aviso que se aceptó.
            vigente = self.context["usuario"].consentimiento_vigente
            if vigente is None or not vigente.aceptado:
                raise serializers.ValidationError(
                    {"detail": "No hay un consentimiento vigente que retirar."}
                )
            aviso = vigente.aviso

        datos["aviso"] = aviso
        return datos


class BajaCuentaSerializer(serializers.Serializer):
    """
    M0.4. Eliminación de la cuenta y de los datos personales asociados.

    Pide la contraseña y una confirmación escrita. Es una operación
    irreversible sobre datos de salud: dos obstáculos deliberados son mejores
    que un arrepentimiento sin vuelta atrás.
    """

    CONFIRMACION = "ELIMINAR"

    password = serializers.CharField(write_only=True)
    confirmacion = serializers.CharField()

    def validate_confirmacion(self, valor):
        if valor.strip().upper() != self.CONFIRMACION:
            raise serializers.ValidationError(
                f'Para confirmar, escribe "{self.CONFIRMACION}".'
            )
        return valor

    def validate_password(self, valor):
        usuario = self.context["usuario"]
        if not usuario.check_password(valor):
            raise serializers.ValidationError("La contraseña no es correcta.")
        return valor


class LogoutSerializer(serializers.Serializer):
    """HU-03. El token de refresco que se va a invalidar."""

    refresh = serializers.CharField(write_only=True)
