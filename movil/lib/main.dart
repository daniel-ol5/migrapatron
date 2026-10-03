import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/almacen_seguro.dart';
import 'core/api_cliente.dart';
import 'core/tema.dart';
import 'estado/estado_bitacora.dart';
import 'estado/estado_sesion.dart';
import 'pantallas/acceso/login.dart';
import 'pantallas/historial/historial.dart';
import 'pantallas/inicio/inicio.dart';
import 'pantallas/perfil/perfil.dart';
import 'servicios/servicio_auth.dart';
import 'servicios/servicio_bitacora.dart';

void main() {
  runApp(const MigraPatronApp());
}

class MigraPatronApp extends StatefulWidget {
  const MigraPatronApp({super.key});

  @override
  State<MigraPatronApp> createState() => _MigraPatronAppState();
}

class _MigraPatronAppState extends State<MigraPatronApp> {
  late final AlmacenSeguro _almacen;
  late final ApiCliente _api;
  late final EstadoSesion _sesion;
  late final EstadoBitacora _bitacora;

  @override
  void initState() {
    super.initState();
    _almacen = AlmacenSeguro();
    _api = ApiCliente(
      almacen: _almacen,
      // Si el refresh también falla, la sesión cae a la pantalla de acceso.
      onSesionExpirada: () => _sesion.resolverArranque(),
    );
    _sesion = EstadoSesion(
      auth: ServicioAuth(api: _api, almacen: _almacen),
    );
    _bitacora = EstadoBitacora(servicio: ServicioBitacora(api: _api));
    _sesion.resolverArranque();
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: _sesion),
        ChangeNotifierProvider.value(value: _bitacora),
      ],
      child: MaterialApp(
        title: 'MigraPatrón',
        debugShowCheckedModeBanner: false,
        theme: Tema.claro(),
        darkTheme: Tema.oscuro(),
        // Sigue la preferencia del teléfono: quien ya lo puso en oscuro por
        // sensibilidad a la luz lo obtiene sin tocar nada.
        themeMode: ThemeMode.system,
        home: const _Router(),
      ),
    );
  }
}

/// Decide qué pantalla mostrar según el estado de la sesión.
class _Router extends StatelessWidget {
  const _Router();

  @override
  Widget build(BuildContext context) {
    final fase = context.watch<EstadoSesion>().fase;

    return switch (fase) {
      FaseSesion.cargando => const _Splash(),
      FaseSesion.fuera => const PantallaLogin(),
      FaseSesion.dentro => const CascaronPrincipal(),
    };
  }
}

class _Splash extends StatelessWidget {
  const _Splash();

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.insights_outlined,
              size: 40,
              color: tema.colorScheme.primary,
            ),
            const SizedBox(height: Esp.lg),
            SizedBox(
              width: 22,
              height: 22,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: tema.colorScheme.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Navegación principal: inicio, historial y perfil.
class CascaronPrincipal extends StatefulWidget {
  const CascaronPrincipal({super.key});

  @override
  State<CascaronPrincipal> createState() => _CascaronPrincipalState();
}

class _CascaronPrincipalState extends State<CascaronPrincipal> {
  int _indice = 0;

  static const _pantallas = [
    PantallaInicio(),
    PantallaHistorial(),
    PantallaPerfil(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pantallas[_indice],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _indice,
        onDestinationSelected: (i) => setState(() => _indice = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.today_outlined),
            selectedIcon: Icon(Icons.today),
            label: 'Hoy',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined),
            selectedIcon: Icon(Icons.calendar_month),
            label: 'Historial',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }
}
