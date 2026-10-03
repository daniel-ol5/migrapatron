"""Vistas de M0 - Gestión de Usuarios y Privacidad."""

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.comun.auditoria import asentar, ip_de

from .models import AvisoPrivacidad, Consentimiento, EventoAuditoria
from .serializers import (
    AvisoPrivacidadSerializer,
    BajaCuentaSerializer,
    CambioConsentimientoSerializer,
    ConsentimientoSerializer,
    LoginSerializer,
    LogoutSerializer,
    PerfilClinicoSerializer,
    RegistroSerializer,
    UsuarioSerializer,
)


def tokens_de(usuario):
    refresh = RefreshToken.for_user(usuario)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class AvisoPrivacidadActualView(APIView):
    """El aviso vigente. Público: hay que poder leerlo antes de registrarse."""

    permission_classes = [permissions.AllowAny]
    serializer_class = AvisoPrivacidadSerializer

    @extend_schema(responses=AvisoPrivacidadSerializer, tags=["M0"])
    def get(self, request):
        aviso = AvisoPrivacidad.actual()
        if aviso is None:
            return Response(
                {"detail": "Todavía no hay un aviso de privacidad publicado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(AvisoPrivacidadSerializer(aviso).data)


class RegistroView(APIView):
    """HU-01. Registro con aceptación del aviso y conservación de la versión."""

    permission_classes = [permissions.AllowAny]
    serializer_class = RegistroSerializer

    @extend_schema(
        request=RegistroSerializer, responses={201: UsuarioSerializer}, tags=["M0"]
    )
    def post(self, request):
        serializer = RegistroSerializer(data=request.data, context={"ip": ip_de(request)})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()

        asentar(
            EventoAuditoria.Accion.REGISTRO,
            usuario=usuario,
            request=request,
            entidad="usuario",
            entidad_id=usuario.pk,
            version_aviso=serializer.validated_data["version_aviso"],
        )

        return Response(
            {**tokens_de(usuario), "usuario": UsuarioSerializer(usuario).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """HU-02. Inicio de sesión mediante autenticación de Django."""

    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer, responses={200: UsuarioSerializer}, tags=["M0"]
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            asentar(
                EventoAuditoria.Accion.ACCESO_FALLIDO,
                request=request,
                email_actor=str(request.data.get("email", ""))[:150],
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario = serializer.validated_data["usuario"]
        usuario.ultimo_acceso = timezone.now()
        usuario.save(update_fields=["ultimo_acceso"])

        asentar(EventoAuditoria.Accion.ACCESO, usuario=usuario, request=request)

        return Response(
            {**tokens_de(usuario), "usuario": UsuarioSerializer(usuario).data}
        )


class LogoutView(APIView):
    """
    HU-03. Cierre de sesión por POST.

    Solo acepta POST. Si aceptara GET, bastaría un enlace o una imagen remota
    para cerrarle la sesión al paciente sin que él lo pidiera.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer, responses={204: None}, tags=["M0"])
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "Falta el token de refresco."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response(
                {"detail": "El token ya no es válido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        asentar(EventoAuditoria.Accion.CIERRE, usuario=request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PerfilView(APIView):
    """HU-04. Consulta y actualización del perfil propio."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UsuarioSerializer

    @extend_schema(responses=UsuarioSerializer, tags=["M0"])
    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)

    @extend_schema(
        request=PerfilClinicoSerializer,
        responses={200: UsuarioSerializer},
        tags=["M0"],
    )
    def patch(self, request):
        usuario = request.user

        # Los datos de identidad se aceptan aquí; el email no, porque es el
        # identificador de la cuenta.
        for campo in ("nombre", "apellido", "fecha_nacimiento", "sexo", "zona_horaria"):
            if campo in request.data:
                setattr(usuario, campo, request.data[campo])
        usuario.save()

        serializer = PerfilClinicoSerializer(
            usuario.perfil, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        asentar(
            EventoAuditoria.Accion.EDICION,
            usuario=usuario,
            request=request,
            entidad="perfil_clinico",
            entidad_id=usuario.perfil.pk,
            campos=sorted(serializer.validated_data.keys()),
        )

        return Response(UsuarioSerializer(usuario).data)


class ConsentimientoView(APIView):
    """HU-04. Historial de consentimiento y cambio de estado."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CambioConsentimientoSerializer

    @extend_schema(responses=ConsentimientoSerializer(many=True), tags=["M0"])
    def get(self, request):
        historial = request.user.consentimientos.select_related("aviso")
        return Response(
            {
                "vigente": request.user.consintio_analisis,
                "historial": ConsentimientoSerializer(historial, many=True).data,
            }
        )

    @extend_schema(
        request=CambioConsentimientoSerializer,
        responses={201: ConsentimientoSerializer},
        tags=["M0"],
    )
    def post(self, request):
        serializer = CambioConsentimientoSerializer(
            data=request.data, context={"usuario": request.user}
        )
        serializer.is_valid(raise_exception=True)

        # Se agrega un hecho nuevo; el anterior no se toca.
        hecho = Consentimiento.objects.create(
            usuario=request.user,
            aviso=serializer.validated_data["aviso"],
            aceptado=serializer.validated_data["aceptado"],
            ip=ip_de(request),
        )

        asentar(
            EventoAuditoria.Accion.CONSENTIMIENTO,
            usuario=request.user,
            request=request,
            entidad="consentimiento",
            entidad_id=hecho.pk,
            aceptado=hecho.aceptado,
            version_aviso=hecho.aviso.version,
        )

        return Response(
            ConsentimientoSerializer(hecho).data, status=status.HTTP_201_CREATED
        )


class BajaCuentaView(APIView):
    """M0.4. Eliminación de la cuenta y de los datos personales asociados."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BajaCuentaSerializer

    @extend_schema(request=BajaCuentaSerializer, responses={200: None}, tags=["M0"])
    def post(self, request):
        serializer = BajaCuentaSerializer(
            data=request.data, context={"usuario": request.user}
        )
        serializer.is_valid(raise_exception=True)

        usuario = request.user
        email = usuario.email
        pk = usuario.pk

        # El asiento se escribe ANTES del borrado: después ya no habría usuario
        # al que asociarlo. Queda con usuario en nulo y el email conservado.
        asentar(
            EventoAuditoria.Accion.BAJA_CUENTA,
            usuario=usuario,
            request=request,
            entidad="usuario",
            entidad_id=pk,
            email_actor=email,
        )

        with transaction.atomic():
            # Los consentimientos protegen el aviso (PROTECT), así que se
            # borran explícitamente antes del usuario.
            usuario.consentimientos.all().delete()
            usuario.delete()

        return Response(
            {"detail": "La cuenta y sus datos fueron eliminados."},
            status=status.HTTP_200_OK,
        )
