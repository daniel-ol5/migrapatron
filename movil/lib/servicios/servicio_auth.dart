import 'package:dio/dio.dart';

import '../core/almacen_seguro.dart';
import '../core/api_cliente.dart';
import '../modelos/usuario.dart';

/// Servicio de M0: registro, sesión, perfil y consentimiento.
class ServicioAuth {
  ServicioAuth({required this.api, required this.almacen});

  final ApiCliente api;
  final AlmacenSeguro almacen;

  Dio get _dio => api.dio;

  /// HU-01. El aviso vigente. Es público: hay que poder leerlo antes de crear
  /// la cuenta.
  Future<AvisoPrivacidad> avisoVigente() async {
    final r = await _dio.get<Map<String, dynamic>>('/auth/aviso-privacidad/');
    return AvisoPrivacidad.desdeJson(r.data!);
  }

  /// HU-01. Registro con aceptación del aviso y conservación de su versión.
  Future<Usuario> registrar({
    required String email,
    required String password,
    required String nombre,
    required String apellido,
    required String versionAviso,
  }) async {
    final r = await _dio.post<Map<String, dynamic>>(
      '/auth/registro/',
      data: {
        'email': email.trim().toLowerCase(),
        'password': password,
        'nombre': nombre.trim(),
        'apellido': apellido.trim(),
        'acepta_aviso': true,
        'version_aviso': versionAviso,
      },
    );
    return _guardarYDevolver(r.data!);
  }

  /// HU-02. Inicio de sesión.
  Future<Usuario> ingresar({
    required String email,
    required String password,
  }) async {
    final r = await _dio.post<Map<String, dynamic>>(
      '/auth/login/',
      data: {'email': email.trim().toLowerCase(), 'password': password},
    );
    return _guardarYDevolver(r.data!);
  }

  Future<Usuario> _guardarYDevolver(Map<String, dynamic> datos) async {
    await almacen.guardarSesion(
      access: datos['access'] as String,
      refresh: datos['refresh'] as String,
    );
    return Usuario.desdeJson(datos['usuario'] as Map<String, dynamic>);
  }

  /// HU-03. Cierre de sesión por POST.
  ///
  /// Los tokens locales se borran incluso si el servidor falla: si no, el
  /// usuario tocó «salir» y se quedaría dentro, que es lo peor que puede pasar
  /// en un teléfono compartido.
  Future<void> salir() async {
    final refresh = await almacen.refresh;
    try {
      if (refresh != null) {
        await _dio.post('/auth/logout/', data: {'refresh': refresh});
      }
    } on DioException {
      // Sin red o token ya vencido: igual se cierra en local.
    } finally {
      await almacen.cerrarSesion();
    }
  }

  /// HU-04. Perfil propio.
  Future<Usuario> perfil() async {
    final r = await _dio.get<Map<String, dynamic>>('/auth/perfil/');
    return Usuario.desdeJson(r.data!);
  }

  /// HU-04. Actualización del perfil.
  Future<Usuario> actualizarPerfil({
    String? nombre,
    String? apellido,
    PerfilClinico? clinico,
  }) async {
    final r = await _dio.patch<Map<String, dynamic>>(
      '/auth/perfil/',
      data: {
        if (nombre != null) 'nombre': nombre.trim(),
        if (apellido != null) 'apellido': apellido.trim(),
        if (clinico != null) ...clinico.aJson(),
      },
    );
    return Usuario.desdeJson(r.data!);
  }

  /// HU-04. Historial de consentimiento: cada cambio es un hecho nuevo.
  Future<(bool, List<HechoConsentimiento>)> historialConsentimiento() async {
    final r = await _dio.get<Map<String, dynamic>>('/auth/consentimiento/');
    final hechos = ((r.data!['historial'] as List?) ?? const [])
        .map((h) => HechoConsentimiento.desdeJson(h as Map<String, dynamic>))
        .toList();
    return (r.data!['vigente'] as bool? ?? false, hechos);
  }

  /// HU-04. Otorgar o retirar el consentimiento.
  Future<void> cambiarConsentimiento({
    required bool aceptado,
    String? versionAviso,
  }) async {
    await _dio.post(
      '/auth/consentimiento/',
      data: {
        'aceptado': aceptado,
        if (aceptado && versionAviso != null) 'version_aviso': versionAviso,
      },
    );
  }

  /// M0.4. Baja de cuenta. Exige contraseña y confirmación escrita.
  Future<void> eliminarCuenta({required String password}) async {
    await _dio.post(
      '/auth/baja/',
      data: {'password': password, 'confirmacion': 'ELIMINAR'},
    );
    await almacen.cerrarSesion();
  }
}
