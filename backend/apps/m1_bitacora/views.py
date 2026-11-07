"""
Vistas de M1 - Seguimiento y Bitácora Diaria.

Todas heredan el aislamiento de `QuerysetPropioMixin`: el queryset se filtra
siempre por el usuario de la sesión. La consecuencia buscada es que pedir un
registro ajeno devuelva 404 y no 403 — un 403 confirmaría que ese registro
existe, y eso ya es información que no corresponde dar.
"""

from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comun.auditoria import asentar
from apps.comun.permisos import QuerysetPropioMixin
from apps.m0_usuarios.models import EventoAuditoria

from .models import AlertaBanderaRoja, Episodio, RegistroDiario
from .serializers import (
    AlertaBanderaRojaSerializer,
    DiaHistorialSerializer,
    EpisodioSerializer,
    RegistroDiarioSerializer,
)


# ------------------------------------------------------------------ bitácora
class RegistroDiarioListCreateView(QuerysetPropioMixin, generics.ListCreateAPIView):
    """HU-05 (alta) y HU-07 (lista)."""

    serializer_class = RegistroDiarioSerializer
    queryset = RegistroDiario.objects.all()

    @extend_schema(tags=["M1"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["M1"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        registro = serializer.save(usuario=self.request.user)
        # Un episodio ya cargado para ese día queda vinculado a esta bitácora.
        for episodio in Episodio.objects.filter(
            usuario=self.request.user,
            registro_diario__isnull=True,
            inicio__date=registro.fecha,
        ):
            episodio.registro_diario = registro
            episodio.save(update_fields=["registro_diario"])

        asentar(
            EventoAuditoria.Accion.CREACION,
            usuario=self.request.user,
            request=self.request,
            entidad="registro_diario",
            entidad_id=registro.pk,
            fecha=str(registro.fecha),
            completado=registro.completado,
        )


class RegistroDiarioDetalleView(
    QuerysetPropioMixin, generics.RetrieveUpdateDestroyAPIView
):
    """HU-08 (edición) y HU-09 (eliminación)."""

    serializer_class = RegistroDiarioSerializer
    queryset = RegistroDiario.objects.all()

    @extend_schema(tags=["M1"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["M1"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def perform_update(self, serializer):
        registro = serializer.save()
        asentar(
            EventoAuditoria.Accion.EDICION,
            usuario=self.request.user,
            request=self.request,
            entidad="registro_diario",
            entidad_id=registro.pk,
            campos=sorted(serializer.validated_data.keys()),
            completado=registro.completado,
        )

    def perform_destroy(self, instance):
        """
        HU-09. Los episodios del día NO se borran con la bitácora.

        El modelo usa SET_NULL: el episodio pierde su contexto diario pero se
        conserva, porque es el dato clínico más valioso del sistema.
        """
        episodios_afectados = instance.episodios.count()
        asentar(
            EventoAuditoria.Accion.ELIMINACION,
            usuario=self.request.user,
            request=self.request,
            entidad="registro_diario",
            entidad_id=instance.pk,
            fecha=str(instance.fecha),
            episodios_desvinculados=episodios_afectados,
        )
        instance.delete()


class RegistroDiarioPorFechaView(QuerysetPropioMixin, generics.RetrieveAPIView):
    """
    HU-05. Busca la bitácora de un día concreto.

    La app la llama al abrir el formulario: si ya existe, entra en modo edición
    en lugar de intentar un alta que la unicidad va a rechazar.
    """

    serializer_class = RegistroDiarioSerializer
    queryset = RegistroDiario.objects.all()
    lookup_field = "fecha"

    @extend_schema(tags=["M1"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ------------------------------------------------------------------ episodios
class EpisodioListCreateView(QuerysetPropioMixin, generics.ListCreateAPIView):
    """HU-06 (alta) y HU-07 (lista)."""

    serializer_class = EpisodioSerializer
    queryset = Episodio.objects.select_related("registro_diario")

    @extend_schema(tags=["M1"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["M1"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        episodio = serializer.save(usuario=self.request.user)
        episodio.vincular_bitacora()
        episodio.save(update_fields=["registro_diario"])

        # HU-17 / RF-14: Evaluación de bandera roja (cefalea en trueno)
        if episodio.intensidad == 10 and episodio.inicio_subito:
            alerta, _ = AlertaBanderaRoja.objects.get_or_create(
                episodio=episodio,
                defaults={
                    "mensaje": (
                        "Un dolor de cabeza súbito e intenso puede requerir atención urgente. "
                        "Busque servicios de emergencia locales ahora."
                    ),
                },
            )
            asentar(
                EventoAuditoria.Accion.ALERTA_BANDERA_ROJA,
                usuario=self.request.user,
                request=self.request,
                entidad="alerta_bandera_roja",
                entidad_id=alerta.pk,
                episodio_id=episodio.pk,
            )

        asentar(
            EventoAuditoria.Accion.CREACION,
            usuario=self.request.user,
            request=self.request,
            entidad="episodio",
            entidad_id=episodio.pk,
            intensidad=episodio.intensidad,
            vinculado=episodio.registro_diario_id is not None,
        )


class EpisodioDetalleView(QuerysetPropioMixin, generics.RetrieveUpdateDestroyAPIView):
    """HU-08 (edición) y HU-09 (eliminación)."""

    serializer_class = EpisodioSerializer
    queryset = Episodio.objects.select_related("registro_diario")

    @extend_schema(tags=["M1"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["M1"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def perform_update(self, serializer):
        episodio = serializer.save()
        if "inicio" in serializer.validated_data:
            episodio.vincular_bitacora()
            episodio.save(update_fields=["registro_diario"])

        # HU-17 / RF-14: Evaluación de bandera roja
        if episodio.intensidad == 10 and episodio.inicio_subito:
            alerta, _ = AlertaBanderaRoja.objects.get_or_create(
                episodio=episodio,
                defaults={
                    "mensaje": (
                        "Un dolor de cabeza súbito e intenso puede requerir atención urgente. "
                        "Busque servicios de emergencia locales ahora."
                    ),
                },
            )
            asentar(
                EventoAuditoria.Accion.ALERTA_BANDERA_ROJA,
                usuario=self.request.user,
                request=self.request,
                entidad="alerta_bandera_roja",
                entidad_id=alerta.pk,
                episodio_id=episodio.pk,
            )

        asentar(
            EventoAuditoria.Accion.EDICION,
            usuario=self.request.user,
            request=self.request,
            entidad="episodio",
            entidad_id=episodio.pk,
            campos=sorted(serializer.validated_data.keys()),
        )

    def perform_destroy(self, instance):
        asentar(
            EventoAuditoria.Accion.ELIMINACION,
            usuario=self.request.user,
            request=self.request,
            entidad="episodio",
            entidad_id=instance.pk,
            inicio=instance.inicio.isoformat(),
        )
        instance.delete()


# ------------------------------------------------------------------ historial
class HistorialView(APIView):
    """
    HU-07. Historial propio ordenado cronológicamente.

    Devuelve un día por fila, incluyendo los días SIN registrar. Mostrar los
    huecos es parte del valor: el paciente necesita ver qué le falta para que el
    análisis tenga datos suficientes.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("dias", int, description="Días hacia atrás (1-365)."),
        ],
        responses=DiaHistorialSerializer(many=True),
        tags=["M1"],
    )
    def get(self, request):
        try:
            dias = int(request.query_params.get("dias", 30))
        except (TypeError, ValueError):
            return Response(
                {"detail": "El parámetro 'dias' debe ser un número entero."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dias = max(1, min(dias, 365))

        hoy = timezone.localdate()
        desde = hoy - timedelta(days=dias - 1)

        bitacoras = {
            r.fecha: r
            for r in RegistroDiario.objects.filter(
                usuario=request.user, fecha__gte=desde, fecha__lte=hoy
            )
        }

        episodios_por_dia = {}
        for episodio in Episodio.objects.filter(
            usuario=request.user,
            inicio__date__gte=desde,
            inicio__date__lte=hoy,
        ).order_by("-inicio"):
            fecha = timezone.localtime(episodio.inicio).date()
            episodios_por_dia.setdefault(fecha, []).append(episodio)

        filas = []
        for offset in range(dias):
            fecha = hoy - timedelta(days=offset)
            bitacora = bitacoras.get(fecha)
            filas.append(
                {
                    "fecha": fecha,
                    "tiene_bitacora": bitacora is not None,
                    "bitacora_completa": bool(bitacora and bitacora.completado),
                    "bitacora_id": bitacora.pk if bitacora else None,
                    "medicacion_rescate": bool(bitacora and bitacora.medicacion_rescate),
                    "episodios": episodios_por_dia.get(fecha, []),
                }
            )

        completas = sum(1 for f in filas if f["bitacora_completa"])
        total_episodios = sum(len(f["episodios"]) for f in filas)

        return Response(
            {
                "desde": desde,
                "hasta": hoy,
                "bitacoras_completas": completas,
                "total_episodios": total_episodios,
                "dias": DiaHistorialSerializer(filas, many=True).data,
            }
        )


class ConfirmarAlertaBanderaRojaView(APIView):
    """
    HU-17 / RF-14. Confirma la lectura de la alerta de bandera roja.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AlertaBanderaRojaSerializer

    @extend_schema(
        request=None, responses={200: AlertaBanderaRojaSerializer}, tags=["M1", "M4"]
    )
    def post(self, request, pk):
        try:
            alerta = AlertaBanderaRoja.objects.select_related("episodio").get(
                pk=pk, episodio__usuario=request.user
            )
        except AlertaBanderaRoja.DoesNotExist:
            return Response(
                {"detail": "Alerta no encontrada."}, status=status.HTTP_404_NOT_FOUND
            )

        alerta.confirmada = True
        alerta.save(update_fields=["confirmada"])

        asentar(
            EventoAuditoria.Accion.EDICION,
            usuario=request.user,
            request=request,
            entidad="alerta_bandera_roja",
            entidad_id=alerta.pk,
            confirmada=True,
        )

        return Response(AlertaBanderaRojaSerializer(alerta).data)
