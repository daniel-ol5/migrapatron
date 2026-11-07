"""Serializadores de M1 - Seguimiento y Bitácora Diaria."""

from django.utils import timezone
from rest_framework import serializers

from .models import AlertaBanderaRoja, Episodio, RegistroDiario


class RegistroDiarioSerializer(serializers.ModelSerializer):
    """
    HU-05, HU-08. Bitácora del día.

    `usuario` no es un campo del serializador: lo pone la vista desde la sesión.
    Si viniera del cuerpo de la petición, un usuario podría escribir en la
    bitácora de otro.
    """

    class Meta:
        model = RegistroDiario
        fields = [
            "id",
            "fecha",
            "hora_corte",
            "horas_sueno",
            "hidratacion",
            "comida_omitida",
            "estres",
            "horas_pantalla",
            "minutos_actividad",
            "cafeina_tazas",
            "contexto_menstrual",
            "medicacion_rescate",
            "sensaciones_premonitorias",
            "completado",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["id", "completado", "creado_en", "actualizado_en"]

    def validate_fecha(self, valor):
        hoy = timezone.localdate()
        if valor > hoy:
            raise serializers.ValidationError(
                "No se puede registrar una bitácora de un día que no ha pasado."
            )

        # HU-08: la fecha no se puede mover. Cambiarla equivaldría a crear otro
        # día y rompería la unicidad (usuario, fecha).
        if self.instance is not None and valor != self.instance.fecha:
            raise serializers.ValidationError(
                "La fecha de una bitácora no se puede cambiar. "
                "Elimínala y crea la del día correcto."
            )
        return valor

    def validate(self, datos):
        """HU-05. Un registro por usuario y fecha."""
        if self.instance is None:
            usuario = self.context["request"].user
            if RegistroDiario.objects.filter(
                usuario=usuario, fecha=datos.get("fecha")
            ).exists():
                raise serializers.ValidationError(
                    {
                        "fecha": (
                            "Ya registraste este día. Edita el registro existente "
                            "en lugar de crear uno nuevo."
                        )
                    }
                )
        return datos


class AlertaBanderaRojaSerializer(serializers.ModelSerializer):
    """HU-17 / RF-14. Alerta médica prioritaria de bandera roja."""

    class Meta:
        model = AlertaBanderaRoja
        fields = ["id", "tipo", "mensaje", "confirmada", "creada_en"]
        read_only_fields = ["id", "tipo", "mensaje", "creada_en"]


class EpisodioSerializer(serializers.ModelSerializer):
    """HU-06, HU-08, HU-17. Episodio con intensidad, inicio súbito y síntomas."""

    en_curso = serializers.BooleanField(read_only=True)
    sintomas_presentes = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )
    fecha_bitacora = serializers.DateField(
        source="registro_diario.fecha", read_only=True, allow_null=True
    )
    alerta_bandera_roja = AlertaBanderaRojaSerializer(read_only=True)

    class Meta:
        model = Episodio
        fields = [
            "id",
            "inicio",
            "inicio_subito",
            "duracion_min",
            "intensidad",
            "nauseas",
            "vomitos",
            "sensibilidad_luz",
            "sensibilidad_sonido",
            "observacion",
            "en_curso",
            "sintomas_presentes",
            "fecha_bitacora",
            "alerta_bandera_roja",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = [
            "id",
            "en_curso",
            "sintomas_presentes",
            "fecha_bitacora",
            "alerta_bandera_roja",
            "creado_en",
            "actualizado_en",
        ]

    def validate_inicio(self, valor):
        if valor > timezone.now():
            raise serializers.ValidationError(
                "El inicio del episodio no puede estar en el futuro."
            )
        return valor

    def validate_intensidad(self, valor):
        if not 1 <= valor <= 10:
            raise serializers.ValidationError(
                "La intensidad va de 1 a 10 en la escala EVA."
            )
        return valor

    def validate(self, datos):
        """Coherencia clínica: no se vomita sin náuseas."""
        vomitos = datos.get("vomitos", getattr(self.instance, "vomitos", False))
        nauseas = datos.get("nauseas", getattr(self.instance, "nauseas", False))
        if vomitos and not nauseas:
            raise serializers.ValidationError(
                {"nauseas": "Si hubo vómitos, también hubo náuseas."}
            )
        return datos


class DiaHistorialSerializer(serializers.Serializer):
    """
    HU-07. Una fila del historial cronológico.

    Se arma en la vista a partir de las bitácoras y los episodios del periodo,
    para que el cliente reciba una sola lista ordenada en lugar de tener que
    cruzar dos.
    """

    fecha = serializers.DateField()
    tiene_bitacora = serializers.BooleanField()
    bitacora_completa = serializers.BooleanField()
    bitacora_id = serializers.IntegerField(allow_null=True)
    episodios = EpisodioSerializer(many=True)
    medicacion_rescate = serializers.BooleanField()
