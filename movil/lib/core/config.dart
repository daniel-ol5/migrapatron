import 'package:flutter/foundation.dart'
    show TargetPlatform, defaultTargetPlatform, kIsWeb;

/// Configuración de la app móvil.
class Config {
  const Config._();

  /// URL base del backend.
  ///
  /// El emulador de Android no puede usar `127.0.0.1`, porque ahí vive el
  /// propio emulador: `10.0.2.2` es su alias para el localhost de la máquina
  /// anfitriona. En el navegador y en escritorio, en cambio, `127.0.0.1` es el
  /// host real y es lo correcto.
  ///
  /// Para un teléfono físico o cualquier otro caso, se pasa la URL al compilar:
  ///
  ///   flutter run --dart-define=API_URL=http://192.168.1.50:8000/api
  ///
  /// Se usa `defaultTargetPlatform` y no `Platform` de dart:io porque dart:io
  /// no existe en el navegador: ahí `Platform.isAndroid` lanza
  /// «Unsupported operation» y la app no llega ni a pintar la primera pantalla.
  static String get apiUrl {
    const definida = String.fromEnvironment('API_URL');
    if (definida.isNotEmpty) return definida;

    final enEmuladorAndroid =
        !kIsWeb && defaultTargetPlatform == TargetPlatform.android;
    return enEmuladorAndroid
        ? 'http://10.0.2.2:8000/api'
        : 'http://127.0.0.1:8000/api';
  }

  /// Días que analiza el motor por defecto (M2).
  static const int periodoAnalisisDias = 90;

  /// M2.2. Ventana temporal: cuánto hacia atrás se buscan factores previos a
  /// un episodio, contando desde la hora de corte de cada bitácora.
  static const int ventanaHoras = 48;

  /// M2.1. Criterios mínimos de evidencia antes de analizar.
  ///
  /// Se replican aquí solo para mostrarle al paciente cuánto le falta. La
  /// validación que decide es la del backend: si estos valores se
  /// desincronizan, manda el servidor.
  static const int minimoBitacoras = 20;
  static const int minimoEpisodios = 3;

  /// RNF-07: esta leyenda acompaña siempre a los hallazgos.
  static const String avisoNoCausalidad =
      'Una asociación no demuestra causalidad. '
      'Comenta estos resultados con tu médico.';
}
