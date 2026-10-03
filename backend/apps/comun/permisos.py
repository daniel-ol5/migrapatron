"""
Aislamiento de información entre usuarios.

Es el invariante más importante del sistema: ningún usuario puede ver ni tocar
los datos de otro. Se aplica en dos capas, y las dos son necesarias.
"""

from rest_framework import permissions


class EsDueno(permissions.BasePermission):
    """
    Segunda capa: el objeto que se va a leer o modificar pertenece a quien pide.

    La primera capa es filtrar el queryset por `usuario` en la vista, y por sí
    sola suele bastar. Esta existe porque si alguien algún día escribe una vista
    nueva y olvida el filtro, el permiso todavía detiene el acceso. Dos
    cerrojos independientes para el mismo invariante.
    """

    def has_object_permission(self, request, view, obj):
        propietario = getattr(obj, "usuario", None)
        return propietario is not None and propietario == request.user


class QuerysetPropioMixin:
    """
    Filtra siempre por el usuario de la sesión y asigna la propiedad al crear.

    Las vistas de M1 y M2 heredan de aquí en lugar de repetir el filtro, porque
    un filtro repetido es un filtro que alguna vez se va a olvidar.
    """

    permission_classes = [permissions.IsAuthenticated, EsDueno]

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
