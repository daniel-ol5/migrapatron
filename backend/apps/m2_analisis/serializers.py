"""
Serializadores de M2 - Análisis Inteligente y Predicción Personal Supervisada.
"""

from rest_framework import serializers

from .models import EstimacionRiesgo


class EstadoSuficienciaSerializer(serializers.Serializer):
    """RF-07A y RF-07B. Estado de suficiencia y barra de avance de 60 días."""

    cumple = serializers.BooleanField()
    dias_validos = serializers.IntegerField()
    meta_dias = serializers.IntegerField()
    faltan_dias = serializers.IntegerField()
    dias_con_episodio = serializers.IntegerField()
    meta_episodios = serializers.IntegerField()
    faltan_episodios = serializers.IntegerField()
    dias_sin_episodio = serializers.IntegerField()
    meta_sin_episodio = serializers.IntegerField()
    faltan_sin_episodio = serializers.IntegerField()
    barra_avance_pct = serializers.FloatField()
    mensaje = serializers.CharField()


class AlertaMedicacionSerializer(serializers.Serializer):
    """HU-18 / RF-15. Conteo de rescate y advertencia preventiva en 30 días."""

    total_dias_rescate_30d = serializers.IntegerField()
    umbral_maximo = serializers.IntegerField()
    alerta_activa = serializers.BooleanField()
    mensaje = serializers.CharField()


class FactorPrincipalSerializer(serializers.Serializer):
    """RF-09B. Factor principal en lenguaje determinista no causal."""

    codigo = serializers.CharField()
    nombre = serializers.CharField()
    explicacion = serializers.CharField()
    coeficiente = serializers.FloatField()
    impacto = serializers.FloatField()


class MetricasTecnicasSerializer(serializers.Serializer):
    """RF-09C. Métricas de validación técnica para divulgación progresiva."""

    auc_roc = serializers.FloatField()
    auc_pr = serializers.FloatField()
    brier_score = serializers.FloatField()
    sensibilidad = serializers.FloatField()
    especificidad = serializers.FloatField()
    tamano_entrenamiento = serializers.IntegerField()
    tamano_validacion = serializers.IntegerField()


class EstimacionRiesgoSerializer(serializers.ModelSerializer):
    """RF-09A a RF-09C. Tarjeta visual de estimación con deslinde clínico."""

    class Meta:
        model = EstimacionRiesgo
        fields = [
            "id",
            "horizonte_horas",
            "probabilidad",
            "categoria_visual",
            "factores_principales",
            "advertencia",
            "creada_en",
        ]


class SolicitudAnalisisSerializer(serializers.Serializer):
    """Parámetros de entrada para ejecutar el análisis."""

    horizonte_horas = serializers.ChoiceField(
        choices=[24, 48, 72],
        default=48,
        help_text="Horizonte temporal de predicción en horas (24, 48 o 72).",
    )


class RespuestaAnalisisSerializer(serializers.Serializer):
    """Respuesta unificada de análisis de patrones y riesgo personal."""

    estado = serializers.CharField()
    mensaje = serializers.CharField()
    suficiencia = EstadoSuficienciaSerializer()
    alerta_medicacion = AlertaMedicacionSerializer()
    estimacion = EstimacionRiesgoSerializer(allow_null=True)
    metricas_tecnicas = MetricasTecnicasSerializer(allow_null=True)
    advertencia = serializers.CharField()
