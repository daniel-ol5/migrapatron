import 'package:dio/dio.dart';

import 'almacen_seguro.dart';
import 'config.dart';

/// Cliente HTTP único de la app.
///
/// Adjunta el access token a cada petición y, ante un 401, intenta renovarlo
/// una sola vez con el refresh token. Las peticiones que llegan mientras se
/// renueva esperan en cola, para no disparar varios refresh a la vez.
class ApiCliente {
  ApiCliente({required AlmacenSeguro almacen, Dio? dio, this.onSesionExpirada})
    : _almacen = almacen,
      dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: Config.apiUrl,
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 15),
              contentType: Headers.jsonContentType,
            ),
          ) {
    this.dio.interceptors.add(
      InterceptorsWrapper(onRequest: _alEnviar, onError: _alFallar),
    );
  }

  final Dio dio;
  final AlmacenSeguro _almacen;

  /// Se invoca cuando el refresh también falla: la app debe volver al login.
  final void Function()? onSesionExpirada;

  Future<String>? _renovando;

  Future<void> _alEnviar(
    RequestOptions opciones,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _almacen.access;
    if (token != null) {
      opciones.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(opciones);
  }

  Future<void> _alFallar(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    final peticion = error.requestOptions;
    final esAuthExpirada =
        error.response?.statusCode == 401 &&
        peticion.extra['yaReintentado'] != true &&
        !peticion.path.contains('/auth/');

    if (!esAuthExpirada) {
      handler.next(error);
      return;
    }

    peticion.extra['yaReintentado'] = true;

    try {
      final nuevoToken = await (_renovando ??= _renovarAccess());
      peticion.headers['Authorization'] = 'Bearer $nuevoToken';
      handler.resolve(await dio.fetch(peticion));
    } catch (_) {
      await _almacen.cerrarSesion();
      onSesionExpirada?.call();
      handler.next(error);
    } finally {
      _renovando = null;
    }
  }

  Future<String> _renovarAccess() async {
    final refresh = await _almacen.refresh;
    if (refresh == null) {
      throw StateError('sin refresh token');
    }

    // Instancia limpia: con `dio` entraríamos en bucle de interceptores.
    final limpio = Dio(BaseOptions(baseUrl: Config.apiUrl));
    final respuesta = await limpio.post<Map<String, dynamic>>(
      '/auth/refresh/',
      data: {'refresh': refresh},
    );

    final nuevo = respuesta.data?['access'] as String?;
    if (nuevo == null) {
      throw StateError('el backend no devolvió un access token');
    }
    await _almacen.actualizarAccess(nuevo);
    return nuevo;
  }
}

/// Traduce un error de red al mensaje que se le muestra a la persona.
String mensajeDeError(Object error) {
  if (error is DioException) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.sendTimeout:
        return 'El servidor tardó demasiado en responder. Intenta de nuevo.';
      case DioExceptionType.connectionError:
        return 'No se pudo conectar. Revisa tu conexión a internet.';
      default:
        final datos = error.response?.data;
        if (datos is Map && datos['detail'] is String) {
          return datos['detail'] as String;
        }
        if ((error.response?.statusCode ?? 0) >= 500) {
          return 'El servidor tuvo un problema. Vuelve a intentarlo.';
        }
    }
  }
  return 'Ocurrió un error inesperado.';
}
