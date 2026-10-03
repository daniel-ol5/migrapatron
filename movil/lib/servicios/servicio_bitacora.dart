import 'package:dio/dio.dart';

import '../core/api_cliente.dart';
import '../modelos/bitacora.dart';

/// Servicio de M1: bitácora diaria, episodios e historial.
class ServicioBitacora {
  ServicioBitacora({required this.api});

  final ApiCliente api;

  Dio get _dio => api.dio;

  // ------------------------------------------------------------- bitácora
  /// HU-05. Busca la bitácora de un día. Devuelve null si ese día no tiene.
  ///
  /// La pantalla la llama al abrirse: si existe, entra en modo edición en lugar
  /// de intentar un alta que la unicidad va a rechazar con un 400.
  Future<RegistroDiario?> bitacoraDe(DateTime fecha) async {
    try {
      final r = await _dio.get<Map<String, dynamic>>(
        '/bitacora/fecha/${comoFecha(fecha)}/',
      );
      return RegistroDiario.desdeJson(r.data!);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }

  /// HU-05 (alta) y HU-08 (edición). Decide el método según si ya tiene id.
  Future<RegistroDiario> guardarBitacora(RegistroDiario registro) async {
    final respuesta = registro.esNuevo
        ? await _dio.post<Map<String, dynamic>>(
            '/bitacora/',
            data: registro.aJson(),
          )
        : await _dio.patch<Map<String, dynamic>>(
            '/bitacora/${registro.id}/',
            // Al editar no se envía la fecha: el backend la rechaza si cambia.
            data: registro.aJson(incluirFecha: false),
          );
    return RegistroDiario.desdeJson(respuesta.data!);
  }

  /// HU-09. Eliminación de la bitácora. Los episodios del día se conservan.
  Future<void> eliminarBitacora(int id) async {
    await _dio.delete('/bitacora/$id/');
  }

  // ------------------------------------------------------------- episodios
  /// HU-06 (alta) y HU-08 (edición).
  Future<Episodio> guardarEpisodio(Episodio episodio) async {
    final respuesta = episodio.esNuevo
        ? await _dio.post<Map<String, dynamic>>(
            '/episodios/',
            data: episodio.aJson(),
          )
        : await _dio.patch<Map<String, dynamic>>(
            '/episodios/${episodio.id}/',
            data: episodio.aJson(),
          );
    return Episodio.desdeJson(respuesta.data!);
  }

  /// HU-09. Eliminación del episodio.
  Future<void> eliminarEpisodio(int id) async {
    await _dio.delete('/episodios/$id/');
  }

  // ------------------------------------------------------------- historial
  /// HU-07. Historial propio, con los días sin registrar incluidos.
  Future<Historial> historial({int dias = 30}) async {
    final r = await _dio.get<Map<String, dynamic>>(
      '/historial/',
      queryParameters: {'dias': dias},
    );
    return Historial.desdeJson(r.data!);
  }
}
