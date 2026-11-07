"""
Comando para sembrar un paciente de demostración con historial clínico completo.

Uso:
    python manage.py seed_demo

Crea el usuario 'paciente.demo@migrapatron.ia' (contraseña: 'Demo1234!') con:
- Consentimiento de privacidad v1.0 otorgado y versionado.
- 65 días continuos de bitácoras completas.
- 12 episodios de migraña con diferentes intensidades y síntomas.
- 1 episodio con intensidad 10/10 e inicio súbito (< 1 min) para demostrar HU-17 (Bandera Roja).
- 14 días con medicación de rescate en el último mes para demostrar HU-18 (>10 días).
- Ejecución automática del modelo L2 de M2 con tarjeta visual, factores explicados y métricas.
"""

from datetime import time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.m0_usuarios.models import (
    AvisoPrivacidad,
    Consentimiento,
    PerfilClinico,
    Usuario,
)
from apps.m1_bitacora.models import AlertaBanderaRoja, Episodio, RegistroDiario
from apps.m2_analisis.models import Analisis, EstimacionRiesgo
from apps.m2_analisis.motor import (
    construir_matriz_temporal,
    contar_dias_rescate_30d,
    entrenar_evaluar_modelo_l2,
    verificar_suficiencia_datos,
)


class Command(BaseCommand):
    help = (
        "Siembra un paciente de demostración con 65 días para validar M2, HU-17 y HU-18."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Sembrando paciente de demostración..."))

        # 1. Asegurar aviso de privacidad
        aviso = AvisoPrivacidad.actual()
        if not aviso:
            aviso = AvisoPrivacidad.objects.create(
                version="1.0",
                titulo="Aviso de Privacidad Oficial",
                contenido="Texto legal del aviso de privacidad para el paciente.",
                es_actual=True,
            )

        # 2. Crear o reiniciar paciente
        email = "paciente.demo@migrapatron.ia"
        password = "Demo.Password.2026"
        usuario, creado = Usuario.objects.get_or_create(
            email=email,
            defaults={
                "nombre": "Ana",
                "apellido": "Gómez",
                "sexo": "F",
                "zona_horaria": "America/La_Paz",
            },
        )
        usuario.set_password(password)
        usuario.save()

        PerfilClinico.objects.get_or_create(
            usuario=usuario,
            defaults={
                "tipo_migrana": "CON_AURA",
                "anios_con_migrana": 5,
                "medicacion_habitual": "Propanolol 40mg",
            },
        )

        Consentimiento.objects.get_or_create(
            usuario=usuario,
            aviso=aviso,
            defaults={"aceptado": True},
        )

        # Limpiar registros previos del demo para garantizar reproducibilidad
        RegistroDiario.objects.filter(usuario=usuario).delete()
        Episodio.objects.filter(usuario=usuario).delete()
        Analisis.objects.filter(usuario=usuario).delete()

        # 3. Sembrar 65 días cronológicos
        hoy = timezone.localdate()
        fecha_inicio = hoy - timedelta(days=64)

        registros = []
        for i in range(65):
            f = fecha_inicio + timedelta(days=i)
            # Simular patrón: cada 5 días sueño bajo y estrés alto
            es_dia_estres = i % 5 == 0
            es_dia_rescate = i >= (65 - 12)  # 12 días con rescate en los últimos 30 días

            reg = RegistroDiario.objects.create(
                usuario=usuario,
                fecha=f,
                hora_corte=time(22, 0),
                horas_sueno=5.0 if es_dia_estres else 7.5,
                hidratacion="BAJA" if es_dia_estres else "ALTA",
                comida_omitida=1 if es_dia_estres else 0,
                estres=5 if es_dia_estres else 2,
                horas_pantalla=9.0 if es_dia_estres else 5.5,
                minutos_actividad=15 if es_dia_estres else 45,
                cafeina_tazas=3 if es_dia_estres else 1,
                medicacion_rescate=es_dia_rescate,
                completado=True,
            )
            registros.append(reg)

        # 4. Sembrar 11 episodios ordinarios vinculados a días de estrés/poco sueño
        dias_con_episodio = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
        for idx in dias_con_episodio:
            reg = registros[idx]
            dt_inicio = timezone.make_aware(
                timezone.datetime.combine(reg.fecha, time(15, 30))
            )
            Episodio.objects.create(
                usuario=usuario,
                registro_diario=reg,
                inicio=dt_inicio,
                duracion_min=240,
                intensidad=7,
                inicio_subito=False,
                nauseas=True,
                vomitos=False,
                sensibilidad_luz=True,
                sensibilidad_sonido=True,
                observacion="Dolor pulsátil unilateral en la sien derecha.",
            )

        # 5. Sembrar 1 episodio de bandera roja (HU-17 / RF-14): intensidad 10 + inicio súbito
        reg_trueno = registros[60]
        dt_trueno = timezone.make_aware(
            timezone.datetime.combine(reg_trueno.fecha, time(19, 0))
        )
        ep_trueno = Episodio.objects.create(
            usuario=usuario,
            registro_diario=reg_trueno,
            inicio=dt_trueno,
            duracion_min=90,
            intensidad=10,
            inicio_subito=True,
            nauseas=True,
            sensibilidad_luz=True,
            observacion="Cefalea explosiva de inicio abrupto.",
        )
        AlertaBanderaRoja.objects.create(
            episodio=ep_trueno,
            tipo=AlertaBanderaRoja.Tipo.CEFALEA_EN_TRUENO,
            mensaje=(
                "Un dolor de cabeza súbito e intenso puede requerir atención urgente. "
                "Busque servicios de emergencia locales ahora."
            ),
            confirmada=False,
        )

        # 6. Ejecutar el modelo supervisado L2 (M2)
        suficiencia = verificar_suficiencia_datos(usuario)
        alerta_med = contar_dias_rescate_30d(usuario)

        X, y, df = construir_matriz_temporal(usuario, horizonte_horas=48)
        resultado = entrenar_evaluar_modelo_l2(X, y, df_metadata=df, horizonte_horas=48)

        analisis = Analisis.objects.create(
            usuario=usuario,
            periodo_inicio=registros[0].fecha,
            periodo_fin=registros[-1].fecha,
            bitacoras_analizadas=len(X),
            episodios_analizados=int(y.sum()),
            episodios_vinculados=int(y.sum()),
            ventana_horas=48,
            version_motor="0.1.0-L2",
            parametros={
                "modelo": "LogisticRegression-L2",
                "corte_entrenamiento": "80/20 cronológico",
                "metricas_tecnicas": resultado["metricas_tecnicas"],
            },
            estado=Analisis.Estado.OK,
            mensaje_estado="Análisis y estimación L2 generados exitosamente",
            duracion_ms=120,
        )

        estimacion = EstimacionRiesgo.objects.create(
            analisis=analisis,
            horizonte_horas=48,
            probabilidad=Decimal(str(resultado["estimacion"]["probabilidad"])),
            categoria_visual=resultado["estimacion"]["categoria_visual"],
            factores_principales=resultado["factores_principales"],
            advertencia=resultado["advertencia"],
        )

        self.stdout.write(self.style.SUCCESS("✓ Paciente de demo sembrado exitosamente:"))
        self.stdout.write(f"  - Email: {email}")
        self.stdout.write(f"  - Contraseña: {password}")
        self.stdout.write(
            f"  - Bitácoras: {suficiencia['dias_validos']} días (Suficiencia: {suficiencia['cumple']})"
        )
        self.stdout.write(
            f"  - Días rescate en 30d: {alerta_med['total_dias_rescate_30d']} días (Alerta activa: {alerta_med['alerta_activa']})"
        )
        self.stdout.write(
            f"  - Estimación actual: Riesgo {estimacion.categoria_visual} ({float(estimacion.probabilidad):.1%})"
        )
        self.stdout.write(
            f"  - Bandera roja generada: Episodio #{ep_trueno.id} (Intensidad 10/10 + Inicio súbito)"
        )
        self.stdout.write(
            f"  - Top factores: {[f['nombre'] for f in estimacion.factores_principales]}"
        )
