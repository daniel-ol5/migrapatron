import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_cliente.dart';
import '../../core/tema.dart';
import '../../core/widgets.dart';
import '../../estado/estado_sesion.dart';
import '../../modelos/usuario.dart';

/// HU-04 (perfil y consentimiento), HU-03 (cierre de sesión) y M0.4 (baja).
class PantallaPerfil extends StatefulWidget {
  const PantallaPerfil({super.key});

  @override
  State<PantallaPerfil> createState() => _PantallaPerfilState();
}

class _PantallaPerfilState extends State<PantallaPerfil> {
  List<HechoConsentimiento> _historial = const [];
  bool _cargandoHistorial = true;

  @override
  void initState() {
    super.initState();
    _cargarHistorial();
  }

  Future<void> _cargarHistorial() async {
    setState(() => _cargandoHistorial = true);
    try {
      final (_, hechos) = await context
          .read<EstadoSesion>()
          .auth
          .historialConsentimiento();
      if (mounted) setState(() => _historial = hechos);
    } on DioException {
      // Un fallo acá no debe romper la pantalla: el resto del perfil sirve.
    } finally {
      if (mounted) setState(() => _cargandoHistorial = false);
    }
  }

  Future<void> _editarDatos() async {
    final usuario = context.read<EstadoSesion>().usuario!;
    final resultado = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _HojaEditarPerfil(usuario: usuario),
    );
    if (resultado == true && mounted) {
      await context.read<EstadoSesion>().refrescar();
    }
  }

  Future<void> _cambiarConsentimiento(bool activar) async {
    final sesion = context.read<EstadoSesion>();

    if (!activar) {
      final seguro = await confirmar(
        context,
        titulo: '¿Retirar el consentimiento?',
        mensaje:
            'Dejaremos de buscar patrones en tus datos. Tus registros se '
            'conservan y puedes volver a activarlo cuando quieras.',
        aceptar: 'Retirar',
      );
      if (!seguro) return;
    }

    try {
      String? version;
      if (activar) {
        version = (await sesion.auth.avisoVigente()).version;
      }
      await sesion.auth.cambiarConsentimiento(
        aceptado: activar,
        versionAviso: version,
      );
      await sesion.refrescar();
      await _cargarHistorial();
      if (!mounted) return;
      avisar(
        context,
        activar ? 'Consentimiento activado' : 'Consentimiento retirado',
      );
    } on DioException catch (e) {
      if (mounted) avisar(context, mensajeDeError(e), esError: true);
    }
  }

  Future<void> _salir() async {
    final seguro = await confirmar(
      context,
      titulo: '¿Cerrar sesión?',
      mensaje:
          'Tus datos se quedan guardados. Vas a tener que entrar de nuevo.',
      aceptar: 'Cerrar sesión',
    );
    if (!seguro || !mounted) return;
    await context.read<EstadoSesion>().salir();
  }

  Future<void> _eliminarCuenta() async {
    final password = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => const _HojaBajaCuenta(),
    );
    if (password == null || !mounted) return;

    final sesion = context.read<EstadoSesion>();
    final error = await sesion.eliminarCuenta(password);
    if (error != null && mounted) {
      avisar(context, error, esError: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final sesion = context.watch<EstadoSesion>();
    final usuario = sesion.usuario;
    final tema = Theme.of(context);

    if (usuario == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Mi perfil')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(Esp.md, Esp.md, Esp.md, Esp.xxl),
        children: [
          _Cabecera(usuario: usuario),

          const TituloSeccion('Datos clínicos'),
          Card(
            child: Column(
              children: [
                _Dato(
                  etiqueta: 'Tipo de migraña',
                  valor: usuario.perfil.tipoLegible,
                ),
                const Divider(height: 1),
                _Dato(
                  etiqueta: 'Años con migraña',
                  valor:
                      usuario.perfil.aniosConMigrana?.toString() ?? 'Sin dato',
                ),
                const Divider(height: 1),
                _Dato(
                  etiqueta: 'Diagnóstico médico previo',
                  valor: usuario.perfil.diagnosticoPrevio ? 'Sí' : 'No',
                ),
                const Divider(height: 1),
                _Dato(
                  etiqueta: 'Hora de corte habitual',
                  valor: usuario.perfil.horaCortePreferida.substring(0, 5),
                ),
                const Divider(height: 1),
                _Dato(
                  etiqueta: 'Registro contexto menstrual',
                  valor: usuario.perfil.registraCicloMenstrual ? 'Sí' : 'No',
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.edit_outlined, size: 19),
                  title: const Text('Editar mis datos'),
                  trailing: const Icon(Icons.chevron_right, size: 19),
                  onTap: _editarDatos,
                ),
              ],
            ),
          ),

          const TituloSeccion(
            'Consentimiento',
            ayuda:
                'Cada cambio queda registrado con su fecha. El historial no se '
                'sobrescribe nunca.',
          ),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  value: usuario.consintioAnalisis,
                  onChanged: sesion.ocupado ? null : _cambiarConsentimiento,
                  title: const Text('Analizar mis datos'),
                  subtitle: Text(
                    usuario.consintioAnalisis
                        ? 'Buscamos patrones solo en tu propio diario.'
                        : 'El análisis está desactivado.',
                  ),
                ),
                if (_historial.isNotEmpty) ...[
                  const Divider(height: 1),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(
                      Esp.md,
                      Esp.sm + 2,
                      Esp.md,
                      Esp.sm + 2,
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Historial',
                          style: tema.textTheme.labelMedium?.copyWith(
                            color: tema.colorScheme.onSurfaceVariant,
                          ),
                        ),
                        const SizedBox(height: Esp.sm),
                        for (final hecho in _historial.take(6))
                          Padding(
                            padding: const EdgeInsets.only(bottom: Esp.xs + 2),
                            child: Row(
                              children: [
                                Icon(
                                  hecho.aceptado
                                      ? Icons.check_circle_outline
                                      : Icons.cancel_outlined,
                                  size: 15,
                                  color: hecho.aceptado
                                      ? Paleta.exito
                                      : tema.colorScheme.onSurfaceVariant,
                                ),
                                const SizedBox(width: Esp.sm),
                                Expanded(
                                  child: Text(
                                    hecho.aceptado
                                        ? 'Aceptado (aviso ${hecho.avisoVersion})'
                                        : 'Retirado',
                                    style: tema.textTheme.bodySmall,
                                  ),
                                ),
                                Text(
                                  _fechaHora(hecho.otorgadoEn),
                                  style: tema.textTheme.bodySmall?.copyWith(
                                    color: tema.colorScheme.onSurfaceVariant,
                                    fontSize: 11.5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ),
                ] else if (_cargandoHistorial)
                  const Padding(
                    padding: EdgeInsets.all(Esp.md),
                    child: Center(
                      child: SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                  ),
              ],
            ),
          ),

          const TituloSeccion('Sesión'),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.logout, size: 19),
                  title: const Text('Cerrar sesión'),
                  onTap: sesion.ocupado ? null : _salir,
                ),
                const Divider(height: 1),
                ListTile(
                  leading: Icon(
                    Icons.delete_forever_outlined,
                    size: 19,
                    color: tema.colorScheme.error,
                  ),
                  title: Text(
                    'Eliminar mi cuenta',
                    style: TextStyle(color: tema.colorScheme.error),
                  ),
                  subtitle: const Text('Borra todos tus datos. No se deshace.'),
                  onTap: sesion.ocupado ? null : _eliminarCuenta,
                ),
              ],
            ),
          ),

          const SizedBox(height: Esp.lg),
          const AvisoNoCausalidad(compacto: true),
        ],
      ),
    );
  }
}

class _Cabecera extends StatelessWidget {
  const _Cabecera({required this.usuario});

  final Usuario usuario;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Row(
      children: [
        Container(
          width: 52,
          height: 52,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: tema.colorScheme.surfaceContainerHigh,
            shape: BoxShape.circle,
            border: Border.all(color: tema.colorScheme.outline),
          ),
          child: Text(
            usuario.iniciales,
            style: tema.textTheme.titleMedium?.copyWith(
              color: tema.colorScheme.primary,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        const SizedBox(width: Esp.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(usuario.nombreCompleto, style: tema.textTheme.titleMedium),
              Text(
                usuario.email,
                style: tema.textTheme.bodySmall?.copyWith(
                  color: tema.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _Dato extends StatelessWidget {
  const _Dato({required this.etiqueta, required this.valor});

  final String etiqueta;
  final String valor;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: Esp.md,
        vertical: Esp.sm + 4,
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              etiqueta,
              style: tema.textTheme.bodyMedium?.copyWith(
                color: tema.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          Text(valor, style: tema.textTheme.bodyMedium),
        ],
      ),
    );
  }
}

/// HU-04. Edición de los datos del perfil.
class _HojaEditarPerfil extends StatefulWidget {
  const _HojaEditarPerfil({required this.usuario});

  final Usuario usuario;

  @override
  State<_HojaEditarPerfil> createState() => _HojaEditarPerfilState();
}

class _HojaEditarPerfilState extends State<_HojaEditarPerfil> {
  late final TextEditingController _nombre;
  late final TextEditingController _apellido;
  late final TextEditingController _anios;
  late final TextEditingController _medicacion;
  late String _tipo;
  late bool _diagnostico;
  late bool _ciclo;
  late TimeOfDay _horaCorte;
  bool _guardando = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final p = widget.usuario.perfil;
    _nombre = TextEditingController(text: widget.usuario.nombre);
    _apellido = TextEditingController(text: widget.usuario.apellido);
    _anios = TextEditingController(text: p.aniosConMigrana?.toString() ?? '');
    _medicacion = TextEditingController(text: p.medicacionHabitual);
    _tipo = p.tipoMigrana;
    _diagnostico = p.diagnosticoPrevio;
    _ciclo = p.registraCicloMenstrual;
    final partes = p.horaCortePreferida.split(':');
    _horaCorte = TimeOfDay(
      hour: int.tryParse(partes[0]) ?? 22,
      minute: int.tryParse(partes.length > 1 ? partes[1] : '0') ?? 0,
    );
  }

  @override
  void dispose() {
    _nombre.dispose();
    _apellido.dispose();
    _anios.dispose();
    _medicacion.dispose();
    super.dispose();
  }

  Future<void> _guardar() async {
    setState(() {
      _guardando = true;
      _error = null;
    });

    final hh = _horaCorte.hour.toString().padLeft(2, '0');
    final mm = _horaCorte.minute.toString().padLeft(2, '0');

    try {
      await context.read<EstadoSesion>().auth.actualizarPerfil(
        nombre: _nombre.text,
        apellido: _apellido.text,
        clinico: widget.usuario.perfil.copiar(
          aniosConMigrana: int.tryParse(_anios.text),
          tipoMigrana: _tipo,
          diagnosticoPrevio: _diagnostico,
          medicacionHabitual: _medicacion.text,
          registraCicloMenstrual: _ciclo,
          horaCortePreferida: '$hh:$mm',
        ),
      );
      if (mounted) Navigator.pop(context, true);
    } on DioException catch (e) {
      if (mounted) setState(() => _error = mensajeDeError(e));
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Padding(
      padding: EdgeInsets.fromLTRB(
        Esp.lg,
        0,
        Esp.lg,
        MediaQuery.of(context).viewInsets.bottom + Esp.lg,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Editar mis datos', style: tema.textTheme.titleMedium),
            const SizedBox(height: Esp.lg),

            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _nombre,
                    decoration: const InputDecoration(labelText: 'Nombre'),
                  ),
                ),
                const SizedBox(width: Esp.sm),
                Expanded(
                  child: TextField(
                    controller: _apellido,
                    decoration: const InputDecoration(labelText: 'Apellido'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: Esp.md),

            // El email no se edita: es el identificador de la cuenta.
            TextField(
              enabled: false,
              decoration: InputDecoration(
                labelText: 'Email',
                hintText: widget.usuario.email,
                helperText: 'El email no se puede cambiar.',
              ),
            ),
            const SizedBox(height: Esp.md),

            DropdownButtonFormField<String>(
              initialValue: _tipo,
              decoration: const InputDecoration(labelText: 'Tipo de migraña'),
              items: [
                for (final e in PerfilClinico.etiquetasTipo.entries)
                  DropdownMenuItem(value: e.key, child: Text(e.value)),
              ],
              onChanged: (v) => setState(() => _tipo = v ?? _tipo),
            ),
            const SizedBox(height: Esp.md),

            TextField(
              controller: _anios,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Años con migraña'),
            ),
            const SizedBox(height: Esp.md),

            TextField(
              controller: _medicacion,
              maxLines: 2,
              decoration: const InputDecoration(
                labelText: 'Medicación habitual',
              ),
            ),
            const SizedBox(height: Esp.sm),

            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.schedule_outlined, size: 20),
              title: const Text('Hora de corte habitual'),
              trailing: Text(
                _horaCorte.format(context),
                style: TextStyle(color: tema.colorScheme.primary),
              ),
              onTap: () async {
                final elegida = await showTimePicker(
                  context: context,
                  initialTime: _horaCorte,
                );
                if (elegida != null) setState(() => _horaCorte = elegida);
              },
            ),

            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: _diagnostico,
              onChanged: (v) => setState(() => _diagnostico = v),
              title: const Text('Tengo diagnóstico médico'),
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: _ciclo,
              onChanged: (v) => setState(() => _ciclo = v),
              title: const Text('Quiero registrar contexto menstrual'),
            ),

            if (_error != null) ...[
              const SizedBox(height: Esp.sm),
              Text(
                _error!,
                style: tema.textTheme.bodySmall?.copyWith(
                  color: tema.colorScheme.error,
                ),
              ),
            ],

            const SizedBox(height: Esp.md),
            FilledButton(
              onPressed: _guardando ? null : _guardar,
              child: _guardando
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Guardar cambios'),
            ),
          ],
        ),
      ),
    );
  }
}

/// M0.4. Baja de cuenta: contraseña más confirmación escrita.
class _HojaBajaCuenta extends StatefulWidget {
  const _HojaBajaCuenta();

  @override
  State<_HojaBajaCuenta> createState() => _HojaBajaCuentaState();
}

class _HojaBajaCuentaState extends State<_HojaBajaCuenta> {
  final _password = TextEditingController();
  final _confirmacion = TextEditingController();
  bool _puede = false;

  @override
  void initState() {
    super.initState();
    _confirmacion.addListener(_revisar);
    _password.addListener(_revisar);
  }

  void _revisar() {
    final listo =
        _password.text.isNotEmpty &&
        _confirmacion.text.trim().toUpperCase() == 'ELIMINAR';
    if (listo != _puede) setState(() => _puede = listo);
  }

  @override
  void dispose() {
    _password.dispose();
    _confirmacion.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Padding(
      padding: EdgeInsets.fromLTRB(
        Esp.lg,
        0,
        Esp.lg,
        MediaQuery.of(context).viewInsets.bottom + Esp.lg,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(
                  Icons.warning_amber_outlined,
                  color: tema.colorScheme.error,
                ),
                const SizedBox(width: Esp.sm),
                Expanded(
                  child: Text(
                    'Eliminar mi cuenta',
                    style: tema.textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: Esp.md),
            Text(
              'Se borran tu cuenta, tu perfil, tus bitácoras y tus episodios. '
              'Esta acción no se puede deshacer y no hay forma de recuperar '
              'los datos.',
              style: tema.textTheme.bodyMedium?.copyWith(
                color: tema.colorScheme.onSurfaceVariant,
                height: 1.45,
              ),
            ),
            const SizedBox(height: Esp.lg),

            TextField(
              controller: _password,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Tu contraseña',
                prefixIcon: Icon(Icons.lock_outline, size: 20),
              ),
            ),
            const SizedBox(height: Esp.md),
            TextField(
              controller: _confirmacion,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(
                labelText: 'Escribe ELIMINAR para confirmar',
              ),
            ),

            const SizedBox(height: Esp.lg),
            FilledButton(
              onPressed: _puede
                  ? () => Navigator.pop(context, _password.text)
                  : null,
              style: FilledButton.styleFrom(
                backgroundColor: tema.colorScheme.error,
                foregroundColor: Colors.white,
              ),
              child: const Text('Eliminar mi cuenta definitivamente'),
            ),
            const SizedBox(height: Esp.sm),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar'),
            ),
          ],
        ),
      ),
    );
  }
}

String _fechaHora(DateTime d) {
  final dd = d.day.toString().padLeft(2, '0');
  final mm = d.month.toString().padLeft(2, '0');
  final hh = d.hour.toString().padLeft(2, '0');
  final min = d.minute.toString().padLeft(2, '0');
  return '$dd/$mm $hh:$min';
}
