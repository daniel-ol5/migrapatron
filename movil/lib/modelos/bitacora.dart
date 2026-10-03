/// Modelos de M1 - Seguimiento y Bitácora Diaria.
library;

import 'usuario.dart' show aDouble;

/// Una fecha en el formato que espera el backend: AAAA-MM-DD.
String comoFecha(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-'
    '${d.month.toString().padLeft(2, '0')}-'
    '${d.day.toString().padLeft(2, '0')}';

class RegistroDiario {
  const RegistroDiario({
    this.id,
    required this.fecha,
    required this.horaCorte,
    this.horasSueno,
    this.hidratacion = '',
    this.comidaOmitida,
    this.estres,
    this.horasPantalla,
    this.minutosActividad,
    this.cafeinaTazas,
    this.contextoMenstrual = '',
    this.medicacionRescate = false,
    this.sensacionesPremonitorias = false,
    this.completado = false,
  });

  final int? id;
  final DateTime fecha;

  /// M1.1. La hora a la que se cierra la bitácora del día. M2 la usa para
  /// decidir qué factores son previos a un episodio.
  final String horaCorte;

  final double? horasSueno;
  final String hidratacion;
  final int? comidaOmitida;
  final int? estres;
  final double? horasPantalla;
  final int? minutosActividad;
  final int? cafeinaTazas;

  final String contextoMenstrual;
  final bool medicacionRescate;
  final bool sensacionesPremonitorias;

  /// Solo los días completos cuentan para la suficiencia de datos de M2.
  final bool completado;

  static const opcionesHidratacion = {
    'BAJA': 'Baja',
    'MEDIA': 'Media',
    'ALTA': 'Alta',
  };

  static const opcionesCiclo = {
    'NO_APLICA': 'No aplica',
    'MENSTRUACION': 'Menstruación',
    'FOLICULAR': 'Folicular',
    'OVULACION': 'Ovulación',
    'LUTEA': 'Lútea',
  };

  /// Los siete factores que el backend exige para marcar el día completo.
  /// Se replica aquí para poder mostrar el avance mientras se llena el
  /// formulario, sin esperar la respuesta del servidor.
  int get factoresCompletos {
    var n = 0;
    if (horasSueno != null) n++;
    if (hidratacion.isNotEmpty) n++;
    if (comidaOmitida != null) n++;
    if (estres != null) n++;
    if (horasPantalla != null) n++;
    if (minutosActividad != null) n++;
    if (cafeinaTazas != null) n++;
    return n;
  }

  static const totalFactores = 7;

  bool get esNuevo => id == null;

  factory RegistroDiario.vacio({
    required DateTime fecha,
    String horaCorte = '22:00',
  }) => RegistroDiario(fecha: fecha, horaCorte: horaCorte);

  factory RegistroDiario.desdeJson(Map<String, dynamic> json) => RegistroDiario(
    id: json['id'] as int?,
    fecha: DateTime.parse(json['fecha'] as String),
    horaCorte: json['hora_corte'] as String? ?? '22:00',
    horasSueno: aDouble(json['horas_sueno']),
    hidratacion: json['hidratacion'] as String? ?? '',
    comidaOmitida: json['comida_omitida'] as int?,
    estres: json['estres'] as int?,
    horasPantalla: aDouble(json['horas_pantalla']),
    minutosActividad: json['minutos_actividad'] as int?,
    cafeinaTazas: json['cafeina_tazas'] as int?,
    contextoMenstrual: json['contexto_menstrual'] as String? ?? '',
    medicacionRescate: json['medicacion_rescate'] as bool? ?? false,
    sensacionesPremonitorias:
        json['sensaciones_premonitorias'] as bool? ?? false,
    completado: json['completado'] as bool? ?? false,
  );

  /// El cuerpo que se envía al backend.
  ///
  /// `fecha` se omite al editar: el serializador la rechaza si cambia, y
  /// enviarla igual solo invita a un 400 accidental.
  Map<String, dynamic> aJson({bool incluirFecha = true}) => {
    if (incluirFecha) 'fecha': comoFecha(fecha),
    'hora_corte': horaCorte,
    'horas_sueno': horasSueno?.toStringAsFixed(2),
    'hidratacion': hidratacion,
    'comida_omitida': comidaOmitida,
    'estres': estres,
    'horas_pantalla': horasPantalla?.toStringAsFixed(2),
    'minutos_actividad': minutosActividad,
    'cafeina_tazas': cafeinaTazas,
    'contexto_menstrual': contextoMenstrual,
    'medicacion_rescate': medicacionRescate,
    'sensaciones_premonitorias': sensacionesPremonitorias,
  };

  RegistroDiario copiar({
    DateTime? fecha,
    String? horaCorte,
    double? horasSueno,
    String? hidratacion,
    int? comidaOmitida,
    int? estres,
    double? horasPantalla,
    int? minutosActividad,
    int? cafeinaTazas,
    String? contextoMenstrual,
    bool? medicacionRescate,
    bool? sensacionesPremonitorias,
  }) => RegistroDiario(
    id: id,
    fecha: fecha ?? this.fecha,
    horaCorte: horaCorte ?? this.horaCorte,
    horasSueno: horasSueno ?? this.horasSueno,
    hidratacion: hidratacion ?? this.hidratacion,
    comidaOmitida: comidaOmitida ?? this.comidaOmitida,
    estres: estres ?? this.estres,
    horasPantalla: horasPantalla ?? this.horasPantalla,
    minutosActividad: minutosActividad ?? this.minutosActividad,
    cafeinaTazas: cafeinaTazas ?? this.cafeinaTazas,
    contextoMenstrual: contextoMenstrual ?? this.contextoMenstrual,
    medicacionRescate: medicacionRescate ?? this.medicacionRescate,
    sensacionesPremonitorias:
        sensacionesPremonitorias ?? this.sensacionesPremonitorias,
    completado: completado,
  );
}

class Episodio {
  const Episodio({
    this.id,
    required this.inicio,
    this.duracionMin,
    required this.intensidad,
    this.nauseas = false,
    this.vomitos = false,
    this.sensibilidadLuz = false,
    this.sensibilidadSonido = false,
    this.observacion = '',
    this.sintomasPresentes = const [],
    this.fechaBitacora,
  });

  final int? id;
  final DateTime inicio;
  final int? duracionMin;

  /// Escala EVA de 1 a 10.
  final int intensidad;

  final bool nauseas;
  final bool vomitos;
  final bool sensibilidadLuz;
  final bool sensibilidadSonido;
  final String observacion;

  /// Los síntomas ya traducidos por el backend, listos para mostrar.
  final List<String> sintomasPresentes;

  /// Fecha de la bitácora a la que quedó vinculado, o null si ese día no tiene.
  final DateTime? fechaBitacora;

  bool get enCurso => duracionMin == null;
  bool get esNuevo => id == null;

  String get duracionLegible {
    if (duracionMin == null) return 'En curso';
    final h = duracionMin! ~/ 60;
    final m = duracionMin! % 60;
    if (h == 0) return '$m min';
    if (m == 0) return '$h h';
    return '$h h $m min';
  }

  /// Los síntomas calculados en local, para el formulario antes de guardar.
  List<String> get sintomasLocales => [
    if (nauseas) 'náuseas',
    if (vomitos) 'vómitos',
    if (sensibilidadLuz) 'sensibilidad a la luz',
    if (sensibilidadSonido) 'sensibilidad al sonido',
  ];

  factory Episodio.nuevo() => Episodio(inicio: DateTime.now(), intensidad: 5);

  factory Episodio.desdeJson(Map<String, dynamic> json) => Episodio(
    id: json['id'] as int?,
    inicio: DateTime.parse(json['inicio'] as String).toLocal(),
    duracionMin: json['duracion_min'] as int?,
    intensidad: json['intensidad'] as int,
    nauseas: json['nauseas'] as bool? ?? false,
    vomitos: json['vomitos'] as bool? ?? false,
    sensibilidadLuz: json['sensibilidad_luz'] as bool? ?? false,
    sensibilidadSonido: json['sensibilidad_sonido'] as bool? ?? false,
    observacion: json['observacion'] as String? ?? '',
    sintomasPresentes:
        (json['sintomas_presentes'] as List?)?.cast<String>() ?? const [],
    fechaBitacora: json['fecha_bitacora'] == null
        ? null
        : DateTime.parse(json['fecha_bitacora'] as String),
  );

  Map<String, dynamic> aJson() => {
    'inicio': inicio.toUtc().toIso8601String(),
    'duracion_min': duracionMin,
    'intensidad': intensidad,
    'nauseas': nauseas,
    'vomitos': vomitos,
    'sensibilidad_luz': sensibilidadLuz,
    'sensibilidad_sonido': sensibilidadSonido,
    'observacion': observacion,
  };

  Episodio copiar({
    DateTime? inicio,
    int? duracionMin,
    bool limpiarDuracion = false,
    int? intensidad,
    bool? nauseas,
    bool? vomitos,
    bool? sensibilidadLuz,
    bool? sensibilidadSonido,
    String? observacion,
  }) => Episodio(
    id: id,
    inicio: inicio ?? this.inicio,
    duracionMin: limpiarDuracion ? null : (duracionMin ?? this.duracionMin),
    intensidad: intensidad ?? this.intensidad,
    nauseas: nauseas ?? this.nauseas,
    vomitos: vomitos ?? this.vomitos,
    sensibilidadLuz: sensibilidadLuz ?? this.sensibilidadLuz,
    sensibilidadSonido: sensibilidadSonido ?? this.sensibilidadSonido,
    observacion: observacion ?? this.observacion,
    sintomasPresentes: sintomasPresentes,
    fechaBitacora: fechaBitacora,
  );
}

/// Una fila del historial (HU-07): un día, con o sin registro.
class DiaHistorial {
  const DiaHistorial({
    required this.fecha,
    required this.tieneBitacora,
    required this.bitacoraCompleta,
    this.bitacoraId,
    this.medicacionRescate = false,
    this.episodios = const [],
  });

  final DateTime fecha;
  final bool tieneBitacora;
  final bool bitacoraCompleta;
  final int? bitacoraId;
  final bool medicacionRescate;
  final List<Episodio> episodios;

  bool get tuvoEpisodio => episodios.isNotEmpty;

  factory DiaHistorial.desdeJson(Map<String, dynamic> json) => DiaHistorial(
    fecha: DateTime.parse(json['fecha'] as String),
    tieneBitacora: json['tiene_bitacora'] as bool? ?? false,
    bitacoraCompleta: json['bitacora_completa'] as bool? ?? false,
    bitacoraId: json['bitacora_id'] as int?,
    medicacionRescate: json['medicacion_rescate'] as bool? ?? false,
    episodios: ((json['episodios'] as List?) ?? const [])
        .map((e) => Episodio.desdeJson(e as Map<String, dynamic>))
        .toList(),
  );
}

/// La respuesta completa del historial, con el avance hacia M2.
class Historial {
  const Historial({
    required this.dias,
    required this.bitacorasCompletas,
    required this.totalEpisodios,
  });

  final List<DiaHistorial> dias;
  final int bitacorasCompletas;
  final int totalEpisodios;

  /// M2.1 exige 20 bitácoras y 3 episodios antes de analizar.
  static const minimoBitacoras = 20;
  static const minimoEpisodios = 3;

  bool get puedeAnalizar =>
      bitacorasCompletas >= minimoBitacoras &&
      totalEpisodios >= minimoEpisodios;

  int get faltanBitacoras =>
      (minimoBitacoras - bitacorasCompletas).clamp(0, minimoBitacoras);

  int get faltanEpisodios =>
      (minimoEpisodios - totalEpisodios).clamp(0, minimoEpisodios);

  factory Historial.desdeJson(Map<String, dynamic> json) => Historial(
    dias: ((json['dias'] as List?) ?? const [])
        .map((d) => DiaHistorial.desdeJson(d as Map<String, dynamic>))
        .toList(),
    bitacorasCompletas: json['bitacoras_completas'] as int? ?? 0,
    totalEpisodios: json['total_episodios'] as int? ?? 0,
  );
}
