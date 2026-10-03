import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../core/api_cliente.dart';
import '../modelos/bitacora.dart';
import '../servicios/servicio_bitacora.dart';

/// Estado del historial y del avance hacia el análisis.
///
/// Las pantallas de alta y edición llaman a `recargar()` al guardar, para que el
/// inicio y el historial queden al día sin que cada una tenga que avisarle a la
/// otra.
class EstadoBitacora extends ChangeNotifier {
  EstadoBitacora({required this.servicio});

  final ServicioBitacora servicio;

  Historial? _historial;
  bool _cargando = false;
  String? _error;
  int _dias = 30;

  Historial? get historial => _historial;
  bool get cargando => _cargando;
  String? get error => _error;
  int get dias => _dias;

  List<DiaHistorial> get diasVisibles => _historial?.dias ?? const [];

  Future<void> recargar({int? dias}) async {
    if (dias != null) _dias = dias;
    _cargando = true;
    _error = null;
    notifyListeners();

    try {
      _historial = await servicio.historial(dias: _dias);
    } on DioException catch (e) {
      _error = mensajeDeError(e);
    } finally {
      _cargando = false;
      notifyListeners();
    }
  }

  /// El día de hoy dentro del historial cargado, si ya se cargó.
  DiaHistorial? get hoy {
    final ahora = DateTime.now();
    for (final dia in diasVisibles) {
      if (dia.fecha.year == ahora.year &&
          dia.fecha.month == ahora.month &&
          dia.fecha.day == ahora.day) {
        return dia;
      }
    }
    return null;
  }

  bool get hoyRegistrado => hoy?.tieneBitacora ?? false;

  /// Los episodios del periodo, ordenados del más reciente al más antiguo.
  List<Episodio> get episodiosRecientes =>
      diasVisibles.expand((d) => d.episodios).toList();
}
