/// Modelos de M0 - Gestión de Usuarios y Privacidad.
library;

/// Convierte a double lo que el backend envía como texto.
///
/// DecimalField de DRF se serializa como String ("6.50"), no como número. Sin
/// esta conversión cada campo decimal estalla con un error de tipo en runtime.
double? aDouble(Object? valor) {
  if (valor == null) return null;
  if (valor is num) return valor.toDouble();
  return double.tryParse(valor.toString());
}

class PerfilClinico {
  const PerfilClinico({
    this.aniosConMigrana,
    this.diagnosticoPrevio = false,
    this.tipoMigrana = 'DESCONOCIDA',
    this.medicacionHabitual = '',
    this.registraCicloMenstrual = false,
    this.horaCortePreferida = '22:00:00',
  });

  final int? aniosConMigrana;
  final bool diagnosticoPrevio;
  final String tipoMigrana;
  final String medicacionHabitual;
  final bool registraCicloMenstrual;
  final String horaCortePreferida;

  static const etiquetasTipo = {
    'CON_AURA': 'Con aura',
    'SIN_AURA': 'Sin aura',
    'CRONICA': 'Crónica',
    'DESCONOCIDA': 'Desconocida',
  };

  String get tipoLegible => etiquetasTipo[tipoMigrana] ?? 'Desconocida';

  factory PerfilClinico.desdeJson(Map<String, dynamic> json) => PerfilClinico(
    aniosConMigrana: json['anios_con_migrana'] as int?,
    diagnosticoPrevio: json['diagnostico_previo'] as bool? ?? false,
    tipoMigrana: json['tipo_migrana'] as String? ?? 'DESCONOCIDA',
    medicacionHabitual: json['medicacion_habitual'] as String? ?? '',
    registraCicloMenstrual: json['registra_ciclo_menstrual'] as bool? ?? false,
    horaCortePreferida: json['hora_corte_preferida'] as String? ?? '22:00:00',
  );

  Map<String, dynamic> aJson() => {
    'anios_con_migrana': aniosConMigrana,
    'diagnostico_previo': diagnosticoPrevio,
    'tipo_migrana': tipoMigrana,
    'medicacion_habitual': medicacionHabitual,
    'registra_ciclo_menstrual': registraCicloMenstrual,
    'hora_corte_preferida': horaCortePreferida,
  };

  PerfilClinico copiar({
    int? aniosConMigrana,
    bool? diagnosticoPrevio,
    String? tipoMigrana,
    String? medicacionHabitual,
    bool? registraCicloMenstrual,
    String? horaCortePreferida,
  }) => PerfilClinico(
    aniosConMigrana: aniosConMigrana ?? this.aniosConMigrana,
    diagnosticoPrevio: diagnosticoPrevio ?? this.diagnosticoPrevio,
    tipoMigrana: tipoMigrana ?? this.tipoMigrana,
    medicacionHabitual: medicacionHabitual ?? this.medicacionHabitual,
    registraCicloMenstrual:
        registraCicloMenstrual ?? this.registraCicloMenstrual,
    horaCortePreferida: horaCortePreferida ?? this.horaCortePreferida,
  );
}

class Usuario {
  const Usuario({
    required this.id,
    required this.email,
    required this.nombre,
    required this.apellido,
    required this.consintioAnalisis,
    this.perfil = const PerfilClinico(),
  });

  final int id;
  final String email;
  final String nombre;
  final String apellido;

  /// RN-01: sin esto en true, M2 no ejecuta el análisis.
  final bool consintioAnalisis;

  final PerfilClinico perfil;

  String get nombreCompleto => '$nombre $apellido'.trim();

  String get iniciales {
    final n = nombre.isNotEmpty ? nombre[0] : '';
    final a = apellido.isNotEmpty ? apellido[0] : '';
    return '$n$a'.toUpperCase();
  }

  factory Usuario.desdeJson(Map<String, dynamic> json) => Usuario(
    id: json['id'] as int,
    email: json['email'] as String,
    nombre: json['nombre'] as String? ?? '',
    apellido: json['apellido'] as String? ?? '',
    consintioAnalisis: json['consintio_analisis'] as bool? ?? false,
    perfil: json['perfil'] == null
        ? const PerfilClinico()
        : PerfilClinico.desdeJson(json['perfil'] as Map<String, dynamic>),
  );
}

class AvisoPrivacidad {
  const AvisoPrivacidad({
    required this.version,
    required this.titulo,
    required this.contenido,
  });

  final String version;
  final String titulo;
  final String contenido;

  factory AvisoPrivacidad.desdeJson(Map<String, dynamic> json) =>
      AvisoPrivacidad(
        version: json['version'] as String,
        titulo: json['titulo'] as String,
        contenido: json['contenido'] as String,
      );
}

/// Un hecho del historial de consentimiento (HU-04).
class HechoConsentimiento {
  const HechoConsentimiento({
    required this.id,
    required this.aceptado,
    required this.avisoVersion,
    required this.otorgadoEn,
  });

  final int id;
  final bool aceptado;
  final String avisoVersion;
  final DateTime otorgadoEn;

  factory HechoConsentimiento.desdeJson(Map<String, dynamic> json) =>
      HechoConsentimiento(
        id: json['id'] as int,
        aceptado: json['aceptado'] as bool,
        avisoVersion: json['aviso_version'] as String? ?? '—',
        otorgadoEn: DateTime.parse(json['otorgado_en'] as String).toLocal(),
      );
}
