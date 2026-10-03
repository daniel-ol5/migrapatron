"""
Publica la versión inicial del aviso de privacidad.

Sin un aviso publicado no se puede registrar a nadie (HU-01 lo exige), así que
este comando es parte de la puesta en marcha:

    python manage.py seed_privacidad
"""

from django.core.management.base import BaseCommand

from apps.m0_usuarios.models import AvisoPrivacidad

VERSION = "1.0"

TEXTO = """\
AVISO DE PRIVACIDAD - MigraPatrón IA

1. QUÉ DATOS GUARDAMOS
   Tu nombre, apellido, email y fecha de nacimiento. Tu contexto clínico: años
   con migraña, tipo diagnosticado y medicación habitual. Y tu diario: horas de
   sueño, hidratación, comidas omitidas, estrés, tiempo de pantalla, actividad
   física, cafeína, contexto menstrual si eliges registrarlo, medicación de
   rescate, sensaciones premonitorias y los episodios con su intensidad y
   síntomas.

2. PARA QUÉ LOS USAMOS
   Únicamente para buscar asociaciones estadísticas EN TUS PROPIOS DATOS y
   mostrártelas explicadas. No entrenamos modelos con los datos de otras
   personas ni usamos los tuyos para entrenar nada que vaya más allá de tu
   cuenta.

3. QUÉ NO HACEMOS
   No vendemos ni compartimos tus datos con terceros. No hacemos publicidad.
   No tenemos acceso médico a tu información: ningún profesional ve tu diario
   salvo que tú le muestres el resumen que generes.

4. QUÉ NO ES ESTE SISTEMA
   MigraPatrón NO diagnostica, NO determina causas y NO recomienda medicación.
   Una asociación estadística no demuestra causalidad. Todo resultado debe
   comentarse con tu médico.

5. TUS DERECHOS
   Puedes consultar y corregir tus datos en cualquier momento. Puedes retirar
   tu consentimiento para el análisis sin perder la cuenta: dejaremos de
   analizar, aunque tus registros se conserven. Y puedes eliminar tu cuenta con
   todos sus datos; esa acción es irreversible.

6. CÓMO LOS PROTEGEMOS
   Tu contraseña se guarda cifrada y nunca en texto legible. Las sesiones usan
   tokens de corta duración. Cada acceso y cada cambio sobre datos clínicos
   queda registrado en una auditoría interna. Tus datos están aislados: ninguna
   otra cuenta puede verlos.

7. CONSERVACIÓN
   Guardamos tus registros mientras tengas la cuenta activa. Al eliminarla,
   borramos tus datos personales y clínicos; se conserva únicamente el asiento
   de auditoría del borrado, sin tu información de salud.

Versión 1.0
"""


class Command(BaseCommand):
    help = "Publica la versión inicial del aviso de privacidad."

    def handle(self, *args, **opciones):
        aviso, creado = AvisoPrivacidad.objects.get_or_create(
            version=VERSION,
            defaults={
                "titulo": "Aviso de Privacidad de MigraPatrón IA",
                "contenido": TEXTO,
                "es_actual": True,
            },
        )

        if creado:
            self.stdout.write(
                self.style.SUCCESS(f"Aviso de privacidad {VERSION} publicado.")
            )
            return

        if not aviso.es_actual:
            aviso.es_actual = True
            aviso.save()
            self.stdout.write(
                self.style.SUCCESS(f"Aviso {VERSION} marcado como vigente.")
            )
            return

        self.stdout.write(f"El aviso {VERSION} ya estaba publicado y vigente.")
