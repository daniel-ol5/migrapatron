import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:migrapatron_movil/core/config.dart';
import 'package:migrapatron_movil/core/tema.dart';
import 'package:migrapatron_movil/core/widgets.dart';
import 'package:migrapatron_movil/modelos/bitacora.dart';
import 'package:migrapatron_movil/modelos/usuario.dart';

/// Envuelve un widget con el tema de la app, para probarlo aislado.
Widget conTema(Widget hijo, {Brightness brillo = Brightness.dark}) {
  return MaterialApp(
    theme: brillo == Brightness.dark ? Tema.oscuro() : Tema.claro(),
    home: Scaffold(body: hijo),
  );
}

void main() {
  // ==================================================== modelos de M1
  group('RegistroDiario', () {
    test('cuenta los factores completos para el avance del formulario', () {
      final vacio = RegistroDiario.vacio(fecha: DateTime(2026, 10, 1));
      expect(vacio.factoresCompletos, 0);

      final parcial = vacio.copiar(horasSueno: 6.5, estres: 4);
      expect(parcial.factoresCompletos, 2);
    });

    test('los siete factores requeridos completan el día', () {
      final lleno = RegistroDiario.vacio(fecha: DateTime(2026, 10, 1)).copiar(
        horasSueno: 6.5,
        hidratacion: 'MEDIA',
        comidaOmitida: 1,
        estres: 4,
        horasPantalla: 8,
        minutosActividad: 20,
        cafeinaTazas: 2,
      );
      expect(lleno.factoresCompletos, RegistroDiario.totalFactores);
    });

    test('el contexto menstrual no cuenta para la completitud', () {
      // Exigirlo dejaría incompletos todos los días de quien no lo registra.
      final conCiclo = RegistroDiario.vacio(
        fecha: DateTime(2026, 10, 1),
      ).copiar(contextoMenstrual: 'MENSTRUACION');
      expect(conCiclo.factoresCompletos, 0);
    });

    test('lee el decimal que el backend envía como texto', () {
      // DecimalField de DRF se serializa como String: "6.50", no 6.5.
      final registro = RegistroDiario.desdeJson({
        'id': 1,
        'fecha': '2026-10-01',
        'hora_corte': '22:00:00',
        'horas_sueno': '6.50',
        'horas_pantalla': '8.25',
        'completado': true,
      });

      expect(registro.horasSueno, 6.5);
      expect(registro.horasPantalla, 8.25);
      expect(registro.completado, isTrue);
    });

    test('omite la fecha al editar, porque el backend la rechaza', () {
      final registro = RegistroDiario.vacio(fecha: DateTime(2026, 10, 1));
      expect(registro.aJson().containsKey('fecha'), isTrue);
      expect(registro.aJson(incluirFecha: false).containsKey('fecha'), isFalse);
    });

    test('formatea la fecha como la espera el backend', () {
      expect(comoFecha(DateTime(2026, 3, 7)), '2026-03-07');
    });
  });

  group('Episodio', () {
    test('sin duración queda en curso', () {
      final abierto = Episodio(inicio: DateTime(2026, 10, 1), intensidad: 7);
      expect(abierto.enCurso, isTrue);
      expect(abierto.duracionLegible, 'En curso');
    });

    test('traduce la duración a horas y minutos', () {
      Episodio con(int min) => Episodio(
        inicio: DateTime(2026, 10, 1),
        intensidad: 5,
        duracionMin: min,
      );

      expect(con(45).duracionLegible, '45 min');
      expect(con(120).duracionLegible, '2 h');
      expect(con(195).duracionLegible, '3 h 15 min');
    });

    test('lista solo los síntomas presentes', () {
      final ep = Episodio(
        inicio: DateTime(2026, 10, 1),
        intensidad: 8,
        nauseas: true,
        sensibilidadLuz: true,
      );

      expect(ep.sintomasLocales, ['náuseas', 'sensibilidad a la luz']);
      expect(ep.sintomasLocales, isNot(contains('vómitos')));
    });

    test('lee los síntomas ya traducidos por el backend', () {
      final ep = Episodio.desdeJson({
        'id': 3,
        'inicio': '2026-10-01T15:00:00Z',
        'intensidad': 9,
        'duracion_min': 180,
        'sintomas_presentes': ['náuseas', 'vómitos'],
        'fecha_bitacora': '2026-10-01',
      });

      expect(ep.sintomasPresentes, ['náuseas', 'vómitos']);
      expect(ep.fechaBitacora, isNotNull);
      expect(ep.enCurso, isFalse);
    });

    test('copiar puede vaciar la duración para reabrir un episodio', () {
      final cerrado = Episodio(
        inicio: DateTime(2026, 10, 1),
        intensidad: 5,
        duracionMin: 120,
      );
      expect(cerrado.copiar(limpiarDuracion: true).enCurso, isTrue);
    });
  });

  // ============================================ suficiencia de datos de M2
  group('Historial y los criterios de M2', () {
    Historial con({required int bitacoras, required int episodios}) =>
        Historial(
          dias: const [],
          bitacorasCompletas: bitacoras,
          totalEpisodios: episodios,
        );

    test('los umbrales son los del documento: 20 bitácoras y 3 episodios', () {
      expect(Historial.minimoBitacoras, 20);
      expect(Historial.minimoEpisodios, 3);
    });

    test('no puede analizar si falta cualquiera de los dos', () {
      expect(con(bitacoras: 19, episodios: 5).puedeAnalizar, isFalse);
      expect(con(bitacoras: 25, episodios: 2).puedeAnalizar, isFalse);
    });

    test('puede analizar al alcanzar los dos mínimos', () {
      expect(con(bitacoras: 20, episodios: 3).puedeAnalizar, isTrue);
    });

    test('calcula cuánto falta sin dar números negativos', () {
      final sobrado = con(bitacoras: 40, episodios: 9);
      expect(sobrado.faltanBitacoras, 0);
      expect(sobrado.faltanEpisodios, 0);

      final corto = con(bitacoras: 12, episodios: 1);
      expect(corto.faltanBitacoras, 8);
      expect(corto.faltanEpisodios, 2);
    });
  });

  // ==================================================== modelos de M0
  group('Usuario y consentimiento', () {
    test('lee el estado del consentimiento que informa el backend', () {
      final u = Usuario.desdeJson({
        'id': 1,
        'email': 'ana@ejemplo.com',
        'nombre': 'Ana',
        'apellido': 'Pérez',
        'consintio_analisis': true,
        'perfil': {'tipo_migrana': 'CON_AURA', 'anios_con_migrana': 7},
      });

      expect(u.consintioAnalisis, isTrue);
      expect(u.nombreCompleto, 'Ana Pérez');
      expect(u.iniciales, 'AP');
      expect(u.perfil.tipoLegible, 'Con aura');
    });

    test('un usuario sin perfil no rompe el parseo', () {
      final u = Usuario.desdeJson({
        'id': 2,
        'email': 'x@y.com',
        'nombre': 'X',
        'apellido': 'Y',
        'consintio_analisis': false,
      });

      expect(u.perfil.tipoMigrana, 'DESCONOCIDA');
      expect(u.consintioAnalisis, isFalse);
    });

    test('un hecho de consentimiento conserva la versión del aviso', () {
      final hecho = HechoConsentimiento.desdeJson({
        'id': 1,
        'aceptado': true,
        'aviso_version': '1.0',
        'otorgado_en': '2026-10-01T12:00:00Z',
      });

      expect(hecho.aceptado, isTrue);
      expect(hecho.avisoVersion, '1.0');
    });
  });

  // ==================================================== sistema de color
  group('Paleta', () {
    test('la escala EVA tiene un color por cada nivel del 1 al 10', () {
      expect(Paleta.escalaEva.length, 10);
    });

    test('la intensidad fuera de rango no estalla', () {
      expect(Paleta.porIntensidad(0), Paleta.escalaEva.first);
      expect(Paleta.porIntensidad(99), Paleta.escalaEva.last);
      expect(Paleta.porIntensidad(1), Paleta.escalaEva.first);
      expect(Paleta.porIntensidad(10), Paleta.escalaEva.last);
    });

    test('la escala de dolor no usa el color de marca', () {
      // Si coincidieran, «botón principal» y «dolor intenso» se confundirían.
      expect(Paleta.escalaEva, isNot(contains(Paleta.primarioOscuro)));
      expect(Paleta.escalaEva, isNot(contains(Paleta.primarioClaro)));
    });

    test('los dos temas definen su propio fondo', () {
      expect(Tema.oscuro().scaffoldBackgroundColor, Paleta.fondoOscuro);
      expect(Tema.claro().scaffoldBackgroundColor, Paleta.fondoClaro);
    });
  });

  // ==================================================== widgets
  group('AvisoNoCausalidad', () {
    testWidgets('muestra la advertencia completa', (tester) async {
      await tester.pumpWidget(conTema(const AvisoNoCausalidad()));

      expect(find.textContaining('no demuestra causalidad'), findsOneWidget);
      expect(find.textContaining('tu médico'), findsOneWidget);
    });

    testWidgets('el texto sale de Config, no está duplicado', (tester) async {
      await tester.pumpWidget(conTema(const AvisoNoCausalidad()));
      expect(find.text(Config.avisoNoCausalidad), findsOneWidget);
    });

    testWidgets('funciona en tema claro y oscuro', (tester) async {
      for (final brillo in [Brightness.light, Brightness.dark]) {
        await tester.pumpWidget(
          conTema(const AvisoNoCausalidad(), brillo: brillo),
        );
        expect(find.byType(AvisoNoCausalidad), findsOneWidget);
      }
    });
  });

  group('InsigniaEva', () {
    testWidgets('muestra el número de la intensidad', (tester) async {
      await tester.pumpWidget(conTema(const InsigniaEva(8)));
      expect(find.text('8'), findsOneWidget);
    });

    testWidgets('cada intensidad del 1 al 10 se dibuja', (tester) async {
      for (var n = 1; n <= 10; n++) {
        await tester.pumpWidget(conTema(InsigniaEva(n)));
        expect(find.text('$n'), findsOneWidget);
      }
    });
  });

  group('EstadoVacio', () {
    testWidgets('muestra título, detalle y acción', (tester) async {
      await tester.pumpWidget(
        conTema(
          EstadoVacio(
            icono: Icons.calendar_today_outlined,
            titulo: 'Nada registrado',
            detalle: 'Empieza hoy.',
            accion: OutlinedButton(
              onPressed: () {},
              child: const Text('Reintentar'),
            ),
          ),
        ),
      );

      expect(find.text('Nada registrado'), findsOneWidget);
      expect(find.text('Empieza hoy.'), findsOneWidget);
      expect(find.text('Reintentar'), findsOneWidget);
    });
  });

  // ==================================================== configuración
  group('Config', () {
    test('los umbrales locales coinciden con los del backend', () {
      expect(Config.minimoBitacoras, Historial.minimoBitacoras);
      expect(Config.minimoEpisodios, Historial.minimoEpisodios);
    });

    test('la ventana temporal es la del documento: 48 horas', () {
      expect(Config.ventanaHoras, 48);
    });

    test('la URL base apunta al backend', () {
      expect(Config.apiUrl, contains('/api'));
    });
  });
}
