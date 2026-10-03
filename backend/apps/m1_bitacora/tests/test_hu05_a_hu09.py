"""
Pruebas de M1 - HU-05 a HU-09.

El grupo más importante es TestHU07Aislamiento: verifica el invariante de que
ningún usuario alcanza los datos de otro, que es la propiedad de seguridad
central del sistema.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.m0_usuarios.models import (
    AvisoPrivacidad,
    Consentimiento,
    EventoAuditoria,
    PerfilClinico,
    Usuario,
)
from apps.m1_bitacora.models import Episodio, RegistroDiario

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------- fixtures
def crear_paciente(email):
    usuario = Usuario.objects.create_user(
        email=email, password="ClaveSegura.2026", nombre="Test", apellido="Paciente"
    )
    PerfilClinico.objects.create(usuario=usuario)
    aviso = AvisoPrivacidad.objects.filter(es_actual=True).first() or (
        AvisoPrivacidad.objects.create(
            version="1.0", titulo="Aviso", contenido="Texto.", es_actual=True
        )
    )
    Consentimiento.objects.create(usuario=usuario, aviso=aviso, aceptado=True)
    return usuario


def cliente_de(usuario):
    cliente = APIClient()
    respuesta = cliente.post(
        reverse("m0_usuarios:login"),
        {"email": usuario.email, "password": "ClaveSegura.2026"},
        format="json",
    )
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.data['access']}")
    return cliente


@pytest.fixture
def ana():
    return crear_paciente("ana@ejemplo.com")


@pytest.fixture
def bruno():
    return crear_paciente("bruno@ejemplo.com")


@pytest.fixture
def api(ana):
    return cliente_de(ana)


@pytest.fixture
def bitacora_valida():
    return {
        "fecha": str(timezone.localdate()),
        "hora_corte": "22:00",
        "horas_sueno": "6.50",
        "hidratacion": "MEDIA",
        "comida_omitida": 1,
        "estres": 4,
        "horas_pantalla": "8.00",
        "minutos_actividad": 20,
        "cafeina_tazas": 2,
        "medicacion_rescate": False,
        "sensaciones_premonitorias": True,
    }


@pytest.fixture
def episodio_valido():
    return {
        "inicio": (timezone.now() - timedelta(hours=3)).isoformat(),
        "duracion_min": 180,
        "intensidad": 7,
        "nauseas": True,
        "vomitos": False,
        "sensibilidad_luz": True,
        "sensibilidad_sonido": False,
    }


# ========================================================== HU-05 Alta diaria
class TestHU05AltaBitacora:
    def test_crea_el_registro_del_dia(self, api, bitacora_valida, ana):
        respuesta = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        assert respuesta.status_code == 201
        assert RegistroDiario.objects.filter(usuario=ana).count() == 1

    def test_marca_completado_cuando_estan_todos_los_factores(self, api, bitacora_valida):
        respuesta = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        assert respuesta.data["completado"] is True

    def test_registro_parcial_queda_incompleto(self, api, bitacora_valida):
        """Solo los días completos cuentan para la suficiencia de datos de M2."""
        del bitacora_valida["estres"]
        del bitacora_valida["cafeina_tazas"]

        respuesta = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        assert respuesta.status_code == 201
        assert respuesta.data["completado"] is False

    def test_rechaza_un_segundo_registro_del_mismo_dia(self, api, bitacora_valida, ana):
        api.post(reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json")
        segundo = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        assert segundo.status_code == 400
        assert RegistroDiario.objects.filter(usuario=ana).count() == 1

    def test_rechaza_una_fecha_futura(self, api, bitacora_valida):
        bitacora_valida["fecha"] = str(timezone.localdate() + timedelta(days=1))

        respuesta = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        assert respuesta.status_code == 400

    @pytest.mark.parametrize(
        "campo,valor",
        [
            ("horas_sueno", "30.00"),
            ("estres", 9),
            ("comida_omitida", 7),
            ("horas_pantalla", "25.00"),
        ],
    )
    def test_rechaza_valores_fuera_de_rango(self, api, bitacora_valida, campo, valor):
        bitacora_valida[campo] = valor

        respuesta = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        assert respuesta.status_code == 400, f"{campo}={valor} debió rechazarse"

    def test_guarda_la_hora_de_corte(self, api, bitacora_valida):
        """M2 la necesita para vincular episodios con la ventana temporal."""
        bitacora_valida["hora_corte"] = "23:30"

        respuesta = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        assert respuesta.data["hora_corte"] == "23:30:00"

    def test_busca_la_bitacora_por_fecha(self, api, bitacora_valida):
        api.post(reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json")

        respuesta = api.get(
            reverse(
                "m1_bitacora:bitacora-por-fecha",
                kwargs={"fecha": bitacora_valida["fecha"]},
            )
        )

        assert respuesta.status_code == 200
        assert respuesta.data["fecha"] == bitacora_valida["fecha"]


# ========================================================= HU-06 Alta episodio
class TestHU06AltaEpisodio:
    def test_crea_el_episodio_con_sus_sintomas(self, api, episodio_valido, ana):
        respuesta = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        assert respuesta.status_code == 201
        episodio = Episodio.objects.get(usuario=ana)
        assert episodio.intensidad == 7
        assert episodio.nauseas is True
        assert episodio.sensibilidad_luz is True

    def test_expone_los_sintomas_en_texto_legible(self, api, episodio_valido):
        respuesta = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        assert "náuseas" in respuesta.data["sintomas_presentes"]
        assert "sensibilidad a la luz" in respuesta.data["sintomas_presentes"]
        assert "vómitos" not in respuesta.data["sintomas_presentes"]

    def test_episodio_sin_duracion_queda_en_curso(self, api, episodio_valido):
        del episodio_valido["duracion_min"]

        respuesta = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        assert respuesta.status_code == 201
        assert respuesta.data["en_curso"] is True

    @pytest.mark.parametrize("intensidad", [0, 11, -3])
    def test_rechaza_intensidad_fuera_de_la_escala_eva(
        self, api, episodio_valido, intensidad
    ):
        episodio_valido["intensidad"] = intensidad

        respuesta = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        assert respuesta.status_code == 400

    def test_rechaza_inicio_futuro(self, api, episodio_valido):
        episodio_valido["inicio"] = (timezone.now() + timedelta(hours=2)).isoformat()

        respuesta = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        assert respuesta.status_code == 400

    def test_rechaza_vomitos_sin_nauseas(self, api, episodio_valido):
        """Coherencia clínica: no se vomita sin haber tenido náuseas."""
        episodio_valido["vomitos"] = True
        episodio_valido["nauseas"] = False

        respuesta = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        assert respuesta.status_code == 400

    def test_se_vincula_a_la_bitacora_del_dia(
        self, api, bitacora_valida, episodio_valido
    ):
        api.post(reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json")

        respuesta = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        assert respuesta.data["fecha_bitacora"] == bitacora_valida["fecha"]

    def test_la_bitacora_posterior_recoge_el_episodio_huerfano(
        self, api, episodio_valido, bitacora_valida
    ):
        """Orden inverso: primero el episodio, después la bitácora del día."""
        api.post(reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json")
        api.post(reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json")

        episodio = Episodio.objects.first()
        assert episodio.registro_diario is not None


# ============================================================ HU-07 Historial
class TestHU07Historial:
    def test_devuelve_los_dias_en_orden_cronologico_inverso(self, api, bitacora_valida):
        api.post(reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json")

        respuesta = api.get(reverse("m1_bitacora:historial"), {"dias": 7})

        assert respuesta.status_code == 200
        fechas = [d["fecha"] for d in respuesta.data["dias"]]
        assert fechas == sorted(fechas, reverse=True)

    def test_muestra_los_dias_sin_registrar(self, api, bitacora_valida):
        """Ver los huecos es parte del valor: el paciente sabe qué le falta."""
        api.post(reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json")

        respuesta = api.get(reverse("m1_bitacora:historial"), {"dias": 10})

        dias = respuesta.data["dias"]
        assert len(dias) == 10
        assert sum(1 for d in dias if d["tiene_bitacora"]) == 1
        assert sum(1 for d in dias if not d["tiene_bitacora"]) == 9

    def test_informa_el_avance_hacia_la_suficiencia_de_datos(
        self, api, bitacora_valida, episodio_valido
    ):
        api.post(reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json")
        api.post(reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json")

        respuesta = api.get(reverse("m1_bitacora:historial"), {"dias": 30})

        assert respuesta.data["bitacoras_completas"] == 1
        assert respuesta.data["total_episodios"] == 1

    def test_acota_el_parametro_dias(self, api):
        respuesta = api.get(reverse("m1_bitacora:historial"), {"dias": 9999})

        assert respuesta.status_code == 200
        assert len(respuesta.data["dias"]) == 365

    def test_rechaza_un_parametro_dias_invalido(self, api):
        respuesta = api.get(reverse("m1_bitacora:historial"), {"dias": "muchos"})

        assert respuesta.status_code == 400

    def test_sin_sesion_no_hay_historial(self):
        assert APIClient().get(reverse("m1_bitacora:historial")).status_code == 401


class TestHU07Aislamiento:
    """
    El invariante central: nadie alcanza los datos de otro.

    Estas son las pruebas que un equipo sin formación en calidad no escribiría,
    y son las que demuestran que el aislamiento funciona de verdad.
    """

    def test_la_lista_solo_trae_lo_propio(self, ana, bruno, bitacora_valida):
        cliente_de(bruno).post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        respuesta = cliente_de(ana).get(reverse("m1_bitacora:bitacora-lista"))

        assert respuesta.data["count"] == 0

    def test_una_bitacora_ajena_responde_no_encontrado(self, ana, bruno, bitacora_valida):
        """
        404, no 403. Un 403 confirmaría que ese registro existe, y eso ya es
        filtrar información sobre otra cuenta.
        """
        creada = cliente_de(bruno).post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )
        ajena = creada.data["id"]

        respuesta = cliente_de(ana).get(
            reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": ajena})
        )

        assert respuesta.status_code == 404

    def test_no_se_puede_editar_una_bitacora_ajena(self, ana, bruno, bitacora_valida):
        creada = cliente_de(bruno).post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        respuesta = cliente_de(ana).patch(
            reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": creada.data["id"]}),
            {"estres": 1},
            format="json",
        )

        assert respuesta.status_code == 404
        assert RegistroDiario.objects.get(pk=creada.data["id"]).estres == 4

    def test_no_se_puede_borrar_una_bitacora_ajena(self, ana, bruno, bitacora_valida):
        creada = cliente_de(bruno).post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        respuesta = cliente_de(ana).delete(
            reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": creada.data["id"]})
        )

        assert respuesta.status_code == 404
        assert RegistroDiario.objects.filter(pk=creada.data["id"]).exists()

    def test_un_episodio_ajeno_responde_no_encontrado(self, ana, bruno, episodio_valido):
        creado = cliente_de(bruno).post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        respuesta = cliente_de(ana).get(
            reverse("m1_bitacora:episodio-detalle", kwargs={"pk": creado.data["id"]})
        )

        assert respuesta.status_code == 404

    def test_no_se_puede_crear_a_nombre_de_otro(self, ana, bruno, bitacora_valida):
        """El usuario sale de la sesión, nunca del cuerpo de la petición."""
        bitacora_valida["usuario"] = bruno.pk

        cliente_de(ana).post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        assert RegistroDiario.objects.filter(usuario=bruno).count() == 0
        assert RegistroDiario.objects.filter(usuario=ana).count() == 1

    def test_los_dos_pueden_registrar_el_mismo_dia(self, ana, bruno, bitacora_valida):
        """La unicidad es por (usuario, fecha), no por fecha."""
        primera = cliente_de(ana).post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )
        segunda = cliente_de(bruno).post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        assert primera.status_code == 201
        assert segunda.status_code == 201


# ============================================================= HU-08 Edición
class TestHU08Edicion:
    def test_edita_la_bitacora_propia(self, api, bitacora_valida):
        creada = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        respuesta = api.patch(
            reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": creada.data["id"]}),
            {"estres": 2, "horas_sueno": "8.00"},
            format="json",
        )

        assert respuesta.status_code == 200
        assert respuesta.data["estres"] == 2

    def test_la_fecha_no_se_puede_cambiar(self, api, bitacora_valida):
        """Moverla equivaldría a crear otro día y rompería la unicidad."""
        creada = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        respuesta = api.patch(
            reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": creada.data["id"]}),
            {"fecha": str(timezone.localdate() - timedelta(days=3))},
            format="json",
        )

        assert respuesta.status_code == 400

    def test_recalcula_la_completitud_al_editar(self, api, bitacora_valida):
        del bitacora_valida["estres"]
        creada = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )
        assert creada.data["completado"] is False

        respuesta = api.patch(
            reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": creada.data["id"]}),
            {"estres": 3},
            format="json",
        )

        assert respuesta.data["completado"] is True

    def test_edita_el_episodio_propio(self, api, episodio_valido):
        creado = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        respuesta = api.patch(
            reverse("m1_bitacora:episodio-detalle", kwargs={"pk": creado.data["id"]}),
            {"intensidad": 9, "duracion_min": 300},
            format="json",
        )

        assert respuesta.status_code == 200
        assert respuesta.data["intensidad"] == 9
        assert respuesta.data["en_curso"] is False

    def test_la_edicion_valida_igual_que_el_alta(self, api, episodio_valido):
        creado = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        respuesta = api.patch(
            reverse("m1_bitacora:episodio-detalle", kwargs={"pk": creado.data["id"]}),
            {"intensidad": 15},
            format="json",
        )

        assert respuesta.status_code == 400

    def test_deja_asiento_de_auditoria(self, api, bitacora_valida):
        creada = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )
        api.patch(
            reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": creada.data["id"]}),
            {"estres": 1},
            format="json",
        )

        assert EventoAuditoria.objects.filter(
            accion=EventoAuditoria.Accion.EDICION, entidad="registro_diario"
        ).exists()


# ========================================================= HU-09 Eliminación
class TestHU09Eliminacion:
    def test_elimina_la_bitacora_propia(self, api, bitacora_valida, ana):
        creada = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )

        respuesta = api.delete(
            reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": creada.data["id"]})
        )

        assert respuesta.status_code == 204
        assert not RegistroDiario.objects.filter(usuario=ana).exists()

    def test_borrar_la_bitacora_conserva_los_episodios_del_dia(
        self, api, bitacora_valida, episodio_valido, ana
    ):
        """
        El episodio es el dato clínico más valioso. Pierde su contexto diario,
        pero no se pierde.
        """
        creada = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )
        api.post(reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json")

        api.delete(
            reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": creada.data["id"]})
        )

        episodio = Episodio.objects.filter(usuario=ana).first()
        assert episodio is not None
        assert episodio.registro_diario is None

    def test_elimina_el_episodio_propio(self, api, episodio_valido, ana):
        creado = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        respuesta = api.delete(
            reverse("m1_bitacora:episodio-detalle", kwargs={"pk": creado.data["id"]})
        )

        assert respuesta.status_code == 204
        assert not Episodio.objects.filter(usuario=ana).exists()

    def test_borrar_un_episodio_no_toca_la_bitacora(
        self, api, bitacora_valida, episodio_valido, ana
    ):
        api.post(reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json")
        creado = api.post(
            reverse("m1_bitacora:episodio-lista"), episodio_valido, format="json"
        )

        api.delete(
            reverse("m1_bitacora:episodio-detalle", kwargs={"pk": creado.data["id"]})
        )

        assert RegistroDiario.objects.filter(usuario=ana).exists()

    def test_el_asiento_de_auditoria_sobrevive_al_borrado(self, api, bitacora_valida):
        creada = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )
        pk = creada.data["id"]

        api.delete(reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": pk}))

        asiento = EventoAuditoria.objects.filter(
            accion=EventoAuditoria.Accion.ELIMINACION, entidad="registro_diario"
        ).first()
        assert asiento is not None
        assert asiento.entidad_id == pk

    def test_borrar_lo_ya_borrado_responde_no_encontrado(self, api, bitacora_valida):
        creada = api.post(
            reverse("m1_bitacora:bitacora-lista"), bitacora_valida, format="json"
        )
        ruta = reverse("m1_bitacora:bitacora-detalle", kwargs={"pk": creada.data["id"]})

        api.delete(ruta)
        segundo = api.delete(ruta)

        assert segundo.status_code == 404
