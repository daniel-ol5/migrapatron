"""
Vistas de M2 - Análisis Inteligente y Predicción Personal Supervisada.

Implementa los requisitos:
- RF-07A y RF-07B: Bloqueo obligatorio antes de 60 días de bitácora válida y balance mínimo.
- RF-08A, RF-08B, RF-08C: Ventanas 0-72h, promedios móviles 30d, modelo supervisado L2 aislado.
- RF-09A, RF-09B, RF-09C: Tarjeta visual de riesgo, 3 factores en lenguaje no causal y divulgación progresiva.
- RF-15 / HU-18: Prevención de cefalea por sobreuso de medicación (>10 días en 30 días).
"""

import time
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comun.auditoria import asentar
from apps.m0_usuarios.models import EventoAuditoria
from apps.m1_bitacora.models import RegistroDiario

from .models import Analisis, EstimacionRiesgo
from .motor import (
    construir_matriz_temporal,
    contar_dias_rescate_30d,
    entrenar_evaluar_modelo_l2,
    verificar_suficiencia_datos,
)
from .serializers import (
    AlertaMedicacionSerializer,
    EstadoSuficienciaSerializer,
    EstimacionRiesgoSerializer,
    RespuestaAnalisisSerializer,
    SolicitudAnalisisSerializer,
)


class EstadoSuficienciaView(APIView):
    """
    RF-07A. Consulta de suficiencia de datos y avance hacia la meta de 60 días.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EstadoSuficienciaSerializer

    @extend_schema(
        responses={200: EstadoSuficienciaSerializer},
        tags=["M2"],
    )
    def get(self, request):
        suficiencia = verificar_suficiencia_datos(request.user)
        return Response(suficiencia, status=status.HTTP_200_OK)


class AlertaMedicacionView(APIView):
    """
    HU-18 / RF-15. Consulta del conteo de medicación de rescate en los últimos 30 días.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AlertaMedicacionSerializer

    @extend_schema(
        responses={200: AlertaMedicacionSerializer},
        tags=["M2", "M3"],
    )
    def get(self, request):
        alerta = contar_dias_rescate_30d(request.user)
        return Response(alerta, status=status.HTTP_200_OK)


class EjecutarAnalisisView(APIView):
    """
    CU-08 / HU-10. Ejecuta el entrenamiento de regresión logística L2 y estima el riesgo personal.
    Si los datos son insuficientes (<60 días o sin balance), bloquea la estimación y devuelve el motivo.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SolicitudAnalisisSerializer

    @extend_schema(
        request=SolicitudAnalisisSerializer,
        responses={200: RespuestaAnalisisSerializer, 201: RespuestaAnalisisSerializer},
        tags=["M2"],
    )
    def post(self, request):
        serializer = SolicitudAnalisisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        horizonte_horas = serializer.validated_data.get("horizonte_horas", 48)

        t_inicio = time.time()
        usuario = request.user

        # 1. Verificar suficiencia no negociable
        suficiencia = verificar_suficiencia_datos(usuario)
        alerta_med = contar_dias_rescate_30d(usuario)

        if not suficiencia["cumple"]:
            # Registro de auditoría y análisis con estado bloqueado
            asentar(
                EventoAuditoria.Accion.ANALISIS,
                usuario=usuario,
                request=request,
                entidad="analisis",
                estado="DATOS_INSUFICIENTES",
                dias_validos=suficiencia["dias_validos"],
            )

            return Response(
                {
                    "estado": Analisis.Estado.DATOS_INSUFICIENTES,
                    "mensaje": suficiencia["mensaje"],
                    "suficiencia": suficiencia,
                    "alerta_medicacion": alerta_med,
                    "estimacion": None,
                    "metricas_tecnicas": None,
                    "advertencia": (
                        "Una asociación no demuestra causalidad. "
                        "Comenta estos resultados con tu médico."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        # 2. Construir series y ventanas sin fuga temporal
        X, y, df = construir_matriz_temporal(usuario, horizonte_horas=horizonte_horas)

        # 3. Entrenar y evaluar modelo L2
        resultado = entrenar_evaluar_modelo_l2(
            X, y, df_metadata=df, horizonte_horas=horizonte_horas
        )

        duracion_ms = int((time.time() - t_inicio) * 1000)

        # 4. Persistir registro de ejecución y estimación
        with transaction.atomic():
            primer_registro = (
                RegistroDiario.objects.filter(usuario=usuario).order_by("fecha").first()
            )
            ultimo_registro = (
                RegistroDiario.objects.filter(usuario=usuario).order_by("-fecha").first()
            )

            analisis = Analisis.objects.create(
                usuario=usuario,
                periodo_inicio=(
                    primer_registro.fecha if primer_registro else timezone.localdate()
                ),
                periodo_fin=(
                    ultimo_registro.fecha if ultimo_registro else timezone.localdate()
                ),
                bitacoras_analizadas=len(X),
                episodios_analizados=int(y.sum()),
                episodios_vinculados=int(y.sum()),
                ventana_horas=horizonte_horas,
                version_motor="0.1.0-L2",
                parametros={
                    "modelo": "LogisticRegression-L2",
                    "corte_entrenamiento": "80/20 cronológico",
                    "horizonte_horas": horizonte_horas,
                },
                estado=Analisis.Estado.OK,
                mensaje_estado="Análisis completado exitosamente",
                duracion_ms=duracion_ms,
            )

            estimacion_obj = EstimacionRiesgo.objects.create(
                analisis=analisis,
                horizonte_horas=horizonte_horas,
                probabilidad=Decimal(str(resultado["estimacion"]["probabilidad"])),
                categoria_visual=resultado["estimacion"]["categoria_visual"],
                factores_principales=resultado["factores_principales"],
                advertencia=resultado["advertencia"],
            )

        asentar(
            EventoAuditoria.Accion.ANALISIS,
            usuario=usuario,
            request=request,
            entidad="analisis",
            entidad_id=analisis.pk,
            categoria_visual=estimacion_obj.categoria_visual,
            probabilidad=float(estimacion_obj.probabilidad),
        )

        return Response(
            {
                "estado": Analisis.Estado.OK,
                "mensaje": "Análisis y estimación generados correctamente.",
                "suficiencia": suficiencia,
                "alerta_medicacion": alerta_med,
                "estimacion": EstimacionRiesgoSerializer(estimacion_obj).data,
                "metricas_tecnicas": resultado["metricas_tecnicas"],
                "advertencia": resultado["advertencia"],
            },
            status=status.HTTP_201_CREATED,
        )


class UltimoAnalisisView(APIView):
    """
    CU-10 / HU-11. Consulta la última estimación generada y el estado actual de suficiencia.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RespuestaAnalisisSerializer

    @extend_schema(responses={200: RespuestaAnalisisSerializer}, tags=["M2"])
    def get(self, request):
        usuario = request.user
        suficiencia = verificar_suficiencia_datos(usuario)
        alerta_med = contar_dias_rescate_30d(usuario)

        ultimo_analisis = (
            Analisis.objects.filter(usuario=usuario, estado=Analisis.Estado.OK)
            .select_related("estimacion_riesgo")
            .first()
        )

        if not ultimo_analisis or not hasattr(ultimo_analisis, "estimacion_riesgo"):
            return Response(
                {
                    "estado": (
                        Analisis.Estado.DATOS_INSUFICIENTES
                        if not suficiencia["cumple"]
                        else "SIN_ANALISIS_PREVIO"
                    ),
                    "mensaje": (
                        suficiencia["mensaje"]
                        if not suficiencia["cumple"]
                        else "Todavía no has generado una estimación."
                    ),
                    "suficiencia": suficiencia,
                    "alerta_medicacion": alerta_med,
                    "estimacion": None,
                    "metricas_tecnicas": None,
                    "advertencia": "Una asociación no demuestra causalidad. Comenta estos resultados con tu médico.",
                },
                status=status.HTTP_200_OK,
            )

        estimacion_obj = ultimo_analisis.estimacion_riesgo
        return Response(
            {
                "estado": Analisis.Estado.OK,
                "mensaje": "Última estimación recuperada.",
                "suficiencia": suficiencia,
                "alerta_medicacion": alerta_med,
                "estimacion": EstimacionRiesgoSerializer(estimacion_obj).data,
                "metricas_tecnicas": ultimo_analisis.parametros.get("metricas_tecnicas"),
                "advertencia": estimacion_obj.advertencia,
            },
            status=status.HTTP_200_OK,
        )
