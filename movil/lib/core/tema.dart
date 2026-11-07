import 'package:flutter/material.dart';

/// Sistema de color de MigraPatrón: paleta «Teal sereno».
///
/// Toda la paleta es de baja luminancia y cromatismo moderado a propósito. La
/// fotofobia es uno de los cuatro síntomas que la app registra, así que la
/// persona que abre esta pantalla puede estar en medio de un episodio y con los
/// ojos sensibles. Por la misma razón el color de marca es un verde azulado y
/// no un azul brillante.
///
/// El verde azulado está reservado a la marca y a las acciones. La escala de
/// intensidad del dolor usa una rampa cálida aparte, para que nunca se confunda
/// «este es el botón principal» con «este dolor fue intenso».
class Paleta {
  const Paleta._();

  // ------------------------------------------------------------ tema oscuro
  static const fondoOscuro = Color(0xFF1B292C);
  static const tarjetaOscuro = Color(0xFF273B40);
  static const tarjetaAltaOscuro = Color(0xFF334C52);
  static const bordeOscuro = Color(0xFF436067);
  static const textoOscuro = Color(0xFFE6F2F7);
  static const apagadoOscuro = Color(0xFF9FBECB);
  static const primarioOscuro = Color(0xFF7BB2D8);

  // ------------------------------------------------------------- tema claro
  static const fondoClaro = Color(0xFFE6F2F7);
  static const tarjetaClaro = Color(0xFFFFFFFF);
  static const tarjetaAltaClaro = Color(0xFFDCEAF2);
  static const bordeClaro = Color(0xFFC3DCE8);
  static const textoClaro = Color(0xFF273B40);
  static const apagadoClaro = Color(0xFF5A757D);
  static const primarioClaro = Color(0xFF4B97C5);

  // ---------------------------------------------------------- semánticos
  // Cálidos y desaturados: un rojo saturado sobre fondo oscuro vibra y cansa
  // la vista, que es exactamente lo que hay que evitar aquí.
  static const exito = Color(0xFF4E9A6B);
  static const aviso = Color(0xFFC08A3E);
  static const error = Color(0xFFC46B6B);
  static const errorClaro = Color(0xFF9B3D3D);

  /// Escala de intensidad del dolor, EVA 1 a 10.
  ///
  /// Va de un amarillo pálido a un rosa profundo. Deliberadamente NO llega al
  /// rojo puro: un 10 ya se comunica por su posición en la escala y por el
  /// número, y saturar el color solo agrega agresión visual.
  static const escalaEva = <Color>[
    Color(0xFFCBC77A), // 1
    Color(0xFFD4BE71), // 2
    Color(0xFFDBB168), // 3
    Color(0xFFDFA263), // 4
    Color(0xFFE09360), // 5
    Color(0xFFDC8361), // 6
    Color(0xFFD57465), // 7
    Color(0xFFC9666A), // 8
    Color(0xFFBA5B6E), // 9
    Color(0xFFA8536F), // 10
  ];

  /// Color para una intensidad EVA. Fuera de rango devuelve los extremos.
  static Color porIntensidad(int eva) {
    final indice = (eva - 1).clamp(0, escalaEva.length - 1);
    return escalaEva[indice];
  }
}

/// Espaciado en una escala de 4, para que los márgenes no se elijan a ojo.
class Esp {
  const Esp._();

  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
  static const xxl = 48.0;
}

class Tema {
  const Tema._();

  static const _radio = 10.0;
  static const _radioGrande = 14.0;

  static ThemeData claro() => _construir(
    brillo: Brightness.light,
    fondo: Paleta.fondoClaro,
    tarjeta: Paleta.tarjetaClaro,
    tarjetaAlta: Paleta.tarjetaAltaClaro,
    borde: Paleta.bordeClaro,
    texto: Paleta.textoClaro,
    apagado: Paleta.apagadoClaro,
    primario: Paleta.primarioClaro,
    sobrePrimario: Colors.white,
    colorError: Paleta.errorClaro,
  );

  static ThemeData oscuro() => _construir(
    brillo: Brightness.dark,
    fondo: Paleta.fondoOscuro,
    tarjeta: Paleta.tarjetaOscuro,
    tarjetaAlta: Paleta.tarjetaAltaOscuro,
    borde: Paleta.bordeOscuro,
    texto: Paleta.textoOscuro,
    apagado: Paleta.apagadoOscuro,
    primario: Paleta.primarioOscuro,
    sobrePrimario: Paleta.fondoOscuro,
    colorError: Paleta.error,
  );

  static ThemeData _construir({
    required Brightness brillo,
    required Color fondo,
    required Color tarjeta,
    required Color tarjetaAlta,
    required Color borde,
    required Color texto,
    required Color apagado,
    required Color primario,
    required Color sobrePrimario,
    required Color colorError,
  }) {
    final esquema = ColorScheme(
      brightness: brillo,
      primary: primario,
      onPrimary: sobrePrimario,
      primaryContainer: tarjetaAlta,
      onPrimaryContainer: texto,
      secondary: primario,
      onSecondary: sobrePrimario,
      tertiary: Paleta.aviso,
      onTertiary: brillo == Brightness.dark ? Paleta.fondoOscuro : Colors.white,
      tertiaryContainer: tarjetaAlta,
      onTertiaryContainer: texto,
      error: colorError,
      onError: Colors.white,
      errorContainer: tarjetaAlta,
      onErrorContainer: colorError,
      surface: fondo,
      onSurface: texto,
      surfaceContainerLowest: fondo,
      surfaceContainerLow: tarjeta,
      surfaceContainer: tarjeta,
      surfaceContainerHigh: tarjetaAlta,
      surfaceContainerHighest: tarjetaAlta,
      onSurfaceVariant: apagado,
      outline: borde,
      outlineVariant: borde,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: esquema,
      scaffoldBackgroundColor: fondo,
      splashFactory: InkSparkle.splashFactory,
    );

    return base.copyWith(
      textTheme: base.textTheme.apply(bodyColor: texto, displayColor: texto),

      appBarTheme: AppBarTheme(
        backgroundColor: fondo,
        foregroundColor: texto,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: texto,
          fontSize: 19,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.2,
        ),
      ),

      cardTheme: CardThemeData(
        color: tarjeta,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(_radioGrande),
          side: BorderSide(color: borde),
        ),
      ),

      dividerTheme: DividerThemeData(color: borde, thickness: 1, space: 1),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: tarjeta,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: Esp.md,
          vertical: 14,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(_radio),
          borderSide: BorderSide(color: borde),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(_radio),
          borderSide: BorderSide(color: borde),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(_radio),
          borderSide: BorderSide(color: primario, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(_radio),
          borderSide: BorderSide(color: colorError),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(_radio),
          borderSide: BorderSide(color: colorError, width: 2),
        ),
        labelStyle: TextStyle(color: apagado),
        hintStyle: TextStyle(color: apagado),
        helperStyle: TextStyle(color: apagado, fontSize: 12),
      ),

      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primario,
          foregroundColor: sobrePrimario,
          minimumSize: const Size.fromHeight(50),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(_radio),
          ),
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primario,
          minimumSize: const Size.fromHeight(50),
          side: BorderSide(color: borde),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(_radio),
          ),
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: primario),
      ),

      sliderTheme: SliderThemeData(
        activeTrackColor: primario,
        inactiveTrackColor: borde,
        thumbColor: primario,
        overlayColor: primario.withValues(alpha: 0.12),
        trackHeight: 4,
      ),

      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (estados) =>
              estados.contains(WidgetState.selected) ? sobrePrimario : apagado,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (estados) =>
              estados.contains(WidgetState.selected) ? primario : tarjetaAlta,
        ),
      ),

      segmentedButtonTheme: SegmentedButtonThemeData(
        style: ButtonStyle(
          side: WidgetStatePropertyAll(BorderSide(color: borde)),
          shape: WidgetStatePropertyAll(
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(_radio)),
          ),
        ),
      ),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: tarjetaAlta,
        contentTextStyle: TextStyle(color: texto),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(_radio),
        ),
      ),

      listTileTheme: ListTileThemeData(
        iconColor: apagado,
        textColor: texto,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(_radio),
        ),
      ),

      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: tarjeta,
        indicatorColor: tarjetaAlta,
        elevation: 0,
        labelTextStyle: WidgetStatePropertyAll(
          TextStyle(fontSize: 11.5, color: apagado),
        ),
      ),

      chipTheme: ChipThemeData(
        backgroundColor: tarjetaAlta,
        side: BorderSide(color: borde),
        labelStyle: TextStyle(color: texto, fontSize: 12.5),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
      ),
    );
  }
}
