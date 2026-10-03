"""
Registro de eventos de auditoría.

Una sola función, para que todos los módulos asienten igual y no haya dos
formas de hacer lo mismo.
"""

from apps.m0_usuarios.models import EventoAuditoria


def ip_de(request):
    """
    IP del cliente, mirando primero la cabecera del proxy.

    `X-Forwarded-For` puede falsificarse, así que esto sirve para auditoría
    forense, no para decisiones de seguridad.
    """
    adelantada = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if adelantada:
        return adelantada.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def asentar(
    accion,
    *,
    usuario=None,
    request=None,
    entidad="",
    entidad_id=None,
    email_actor="",
    **detalle,
):
    """
    Deja un asiento en la auditoría.

    Nunca interrumpe la operación que la llamó: si la auditoría fallara, lo
    correcto es perder el asiento, no el dato clínico del paciente. Por eso el
    except es amplio a propósito.
    """
    if usuario is None and request is not None:
        candidato = getattr(request, "user", None)
        if candidato is not None and candidato.is_authenticated:
            usuario = candidato

    try:
        return EventoAuditoria.objects.create(
            usuario=usuario,
            email_actor=email_actor or (usuario.email if usuario else ""),
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=detalle,
            ip=ip_de(request) if request is not None else None,
        )
    except Exception:  # noqa: BLE001
        return None
