import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../core/api_cliente.dart';
import '../modelos/usuario.dart';
import '../servicios/servicio_auth.dart';

enum FaseSesion { cargando, fuera, dentro }

/// Estado de la sesión del paciente.
///
/// Es la única fuente de verdad sobre quién está dentro. Las pantallas no
/// guardan copias del usuario: lo leen de aquí, para que un cambio de perfil se
/// refleje en todas a la vez.
class EstadoSesion extends ChangeNotifier {
  EstadoSesion({required this.auth});

  final ServicioAuth auth;

  FaseSesion _fase = FaseSesion.cargando;
  Usuario? _usuario;
  bool _ocupado = false;

  FaseSesion get fase => _fase;
  Usuario? get usuario => _usuario;
  bool get ocupado => _ocupado;
  bool get dentro => _fase == FaseSesion.dentro;

  /// Arranque: decide si entrar al inicio o al login.
  ///
  /// Tener un token guardado no garantiza que siga válido, así que se verifica
  /// pidiendo el perfil. Si el token venció y el refresh también, el
  /// interceptor cierra la sesión y aquí se cae a la pantalla de acceso.
  Future<void> resolverArranque() async {
    if (!await auth.almacen.haySesion()) {
      _fase = FaseSesion.fuera;
      notifyListeners();
      return;
    }

    try {
      _usuario = await auth.perfil();
      _fase = FaseSesion.dentro;
    } on DioException {
      await auth.almacen.cerrarSesion();
      _fase = FaseSesion.fuera;
    }
    notifyListeners();
  }

  /// HU-02. Devuelve null si entró; si no, el mensaje a mostrar.
  Future<String?> ingresar({required String email, required String password}) =>
      _intentar(() => auth.ingresar(email: email, password: password));

  /// HU-01.
  Future<String?> registrar({
    required String email,
    required String password,
    required String nombre,
    required String apellido,
    required String versionAviso,
  }) => _intentar(
    () => auth.registrar(
      email: email,
      password: password,
      nombre: nombre,
      apellido: apellido,
      versionAviso: versionAviso,
    ),
  );

  Future<String?> _intentar(Future<Usuario> Function() accion) async {
    _ocupado = true;
    notifyListeners();
    try {
      _usuario = await accion();
      _fase = FaseSesion.dentro;
      return null;
    } on DioException catch (e) {
      return mensajeDeError(e);
    } finally {
      _ocupado = false;
      notifyListeners();
    }
  }

  /// HU-03.
  Future<void> salir() async {
    _ocupado = true;
    notifyListeners();
    await auth.salir();
    _usuario = null;
    _fase = FaseSesion.fuera;
    _ocupado = false;
    notifyListeners();
  }

  /// HU-04. Refresca el usuario tras editar el perfil o el consentimiento.
  Future<void> refrescar() async {
    try {
      _usuario = await auth.perfil();
      notifyListeners();
    } on DioException {
      // Se conserva lo que ya había: un fallo de red no debe vaciar la pantalla.
    }
  }

  /// M0.4. Tras la baja, la sesión queda fuera y sin usuario.
  Future<String?> eliminarCuenta(String password) async {
    _ocupado = true;
    notifyListeners();
    try {
      await auth.eliminarCuenta(password: password);
      _usuario = null;
      _fase = FaseSesion.fuera;
      return null;
    } on DioException catch (e) {
      return mensajeDeError(e);
    } finally {
      _ocupado = false;
      notifyListeners();
    }
  }
}
