import 'dart:io' show Platform;

/// Configuración de la app móvil.
class Config {
  const Config._();

  /// URL base del backend.
  ///
  /// En el emulador de Android, `10.0.2.2` es el alias del `localhost` de la
  /// máquina anfitriona. Para probar en un teléfono físico hay que pasar la IP
  /// LAN al compilar:
  ///
  ///   flutter run --dart-define=API_URL=http://192.168.1.50:8000/api
  static String get apiUrl {
    const definida = String.fromEnvironment('API_URL');
    if (definida.isNotEmpty) return definida;
    if (Platform.isAndroid) return 'http://10.0.2.2:8000/api';
    return 'http://127.0.0.1:8000/api';
  }

  /// Días que analiza el motor por defecto (CU-08).
  static const int periodoAnalisisDias = 90;

  /// Ventana de retraso: el día D se compara con el día D-1.
  static const int lagDias = 1;

  /// Suficiencia de datos (RN-02). Solo para avisar al paciente; la validación
  /// real la hace el backend.
  static const int minimoDias = 14;
  static const int minimoEpisodios = 3;

  /// RNF-07: esta leyenda acompaña siempre a los hallazgos.
  static const String avisoNoCausalidad =
      'Una asociación no demuestra causalidad. '
      'Comenta estos resultados con tu médico.';
}
