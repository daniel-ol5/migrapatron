import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Guarda los tokens de sesión en el almacén cifrado del sistema operativo
/// (Keystore en Android, Keychain en iOS).
///
/// RNF-05: son datos de salud, no van en SharedPreferences.
class AlmacenSeguro {
  // Desde flutter_secure_storage 10 el cifrado en Android es el
  // comportamiento por defecto, así que solo se configura iOS.
  AlmacenSeguro({FlutterSecureStorage? almacen})
    : _almacen =
          almacen ??
          const FlutterSecureStorage(
            iOptions: IOSOptions(
              accessibility: KeychainAccessibility.first_unlock,
            ),
          );

  final FlutterSecureStorage _almacen;

  static const _claveAccess = 'migrapatron.access';
  static const _claveRefresh = 'migrapatron.refresh';

  Future<String?> get access => _almacen.read(key: _claveAccess);

  Future<String?> get refresh => _almacen.read(key: _claveRefresh);

  Future<void> guardarSesion({
    required String access,
    required String refresh,
  }) async {
    await _almacen.write(key: _claveAccess, value: access);
    await _almacen.write(key: _claveRefresh, value: refresh);
  }

  Future<void> actualizarAccess(String access) {
    return _almacen.write(key: _claveAccess, value: access);
  }

  Future<void> cerrarSesion() async {
    await _almacen.delete(key: _claveAccess);
    await _almacen.delete(key: _claveRefresh);
  }

  /// Usado por el splash para decidir a qué pantalla entrar.
  Future<bool> haySesion() async => (await access) != null;
}
