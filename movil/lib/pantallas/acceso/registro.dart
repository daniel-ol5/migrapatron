import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_cliente.dart';
import '../../core/tema.dart';
import '../../core/widgets.dart';
import '../../estado/estado_sesion.dart';
import '../../modelos/usuario.dart';

/// HU-01. Registro con aceptación del aviso de privacidad.
///
/// La pantalla carga el aviso vigente antes de permitir crear la cuenta, y
/// envía su versión junto al registro. Si el aviso cambió mientras la persona
/// llenaba el formulario, el backend rechaza el alta: aceptar un texto que ya
/// no rige no es consentir.
class PantallaRegistro extends StatefulWidget {
  const PantallaRegistro({super.key});

  @override
  State<PantallaRegistro> createState() => _PantallaRegistroState();
}

class _PantallaRegistroState extends State<PantallaRegistro> {
  final _formulario = GlobalKey<FormState>();
  final _nombre = TextEditingController();
  final _apellido = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();

  bool _verPassword = false;
  bool _acepta = false;
  String? _error;

  AvisoPrivacidad? _aviso;
  bool _cargandoAviso = true;
  String? _errorAviso;

  @override
  void initState() {
    super.initState();
    _cargarAviso();
  }

  @override
  void dispose() {
    _nombre.dispose();
    _apellido.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _cargarAviso() async {
    setState(() {
      _cargandoAviso = true;
      _errorAviso = null;
    });
    try {
      final aviso = await context.read<EstadoSesion>().auth.avisoVigente();
      if (mounted) setState(() => _aviso = aviso);
    } on DioException catch (e) {
      if (mounted) setState(() => _errorAviso = mensajeDeError(e));
    } finally {
      if (mounted) setState(() => _cargandoAviso = false);
    }
  }

  Future<void> _registrar() async {
    setState(() => _error = null);
    if (!_formulario.currentState!.validate()) return;

    if (!_acepta) {
      setState(
        () => _error =
            'Hay que aceptar el aviso de privacidad para crear la cuenta.',
      );
      return;
    }

    final mensaje = await context.read<EstadoSesion>().registrar(
      email: _email.text,
      password: _password.text,
      nombre: _nombre.text,
      apellido: _apellido.text,
      versionAviso: _aviso!.version,
    );
    if (mensaje != null && mounted) setState(() => _error = mensaje);
  }

  void _verAvisoCompleto() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.85,
        builder: (ctx, scroll) => Padding(
          padding: const EdgeInsets.fromLTRB(Esp.lg, 0, Esp.lg, Esp.lg),
          child: ListView(
            controller: scroll,
            children: [
              Text(_aviso!.titulo, style: Theme.of(ctx).textTheme.titleMedium),
              const SizedBox(height: Esp.sm),
              Text(
                'Versión ${_aviso!.version}',
                style: Theme.of(ctx).textTheme.bodySmall?.copyWith(
                  color: Theme.of(ctx).colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: Esp.md),
              Text(
                _aviso!.contenido,
                style: Theme.of(
                  ctx,
                ).textTheme.bodyMedium?.copyWith(height: 1.55),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final ocupado = context.watch<EstadoSesion>().ocupado;

    return Scaffold(
      appBar: AppBar(title: const Text('Crear cuenta')),
      body: SafeArea(
        child: _cargandoAviso
            ? const Center(child: CircularProgressIndicator())
            : _errorAviso != null
            ? EstadoVacio(
                icono: Icons.cloud_off_outlined,
                titulo: 'No se pudo cargar el aviso de privacidad',
                detalle: _errorAviso,
                accion: OutlinedButton(
                  onPressed: _cargarAviso,
                  child: const Text('Reintentar'),
                ),
              )
            : SingleChildScrollView(
                padding: const EdgeInsets.all(Esp.lg),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 420),
                    child: Form(
                      key: _formulario,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: TextFormField(
                                  controller: _nombre,
                                  textCapitalization: TextCapitalization.words,
                                  enabled: !ocupado,
                                  decoration: const InputDecoration(
                                    labelText: 'Nombre',
                                  ),
                                  validator: (v) => (v ?? '').trim().isEmpty
                                      ? 'Obligatorio'
                                      : null,
                                ),
                              ),
                              const SizedBox(width: Esp.sm),
                              Expanded(
                                child: TextFormField(
                                  controller: _apellido,
                                  textCapitalization: TextCapitalization.words,
                                  enabled: !ocupado,
                                  decoration: const InputDecoration(
                                    labelText: 'Apellido',
                                  ),
                                  validator: (v) => (v ?? '').trim().isEmpty
                                      ? 'Obligatorio'
                                      : null,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: Esp.md),

                          TextFormField(
                            controller: _email,
                            keyboardType: TextInputType.emailAddress,
                            enabled: !ocupado,
                            decoration: const InputDecoration(
                              labelText: 'Email',
                              helperText: 'Con este email vas a entrar.',
                            ),
                            validator: (v) {
                              final texto = (v ?? '').trim();
                              if (texto.isEmpty) return 'Escribe tu email.';
                              if (!texto.contains('@') ||
                                  !texto.contains('.')) {
                                return 'Ese email no parece válido.';
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: Esp.md),

                          TextFormField(
                            controller: _password,
                            obscureText: !_verPassword,
                            enabled: !ocupado,
                            decoration: InputDecoration(
                              labelText: 'Contraseña',
                              helperText:
                                  'Mínimo 8 caracteres. Evita algo fácil '
                                  'de adivinar.',
                              helperMaxLines: 2,
                              suffixIcon: IconButton(
                                icon: Icon(
                                  _verPassword
                                      ? Icons.visibility_off_outlined
                                      : Icons.visibility_outlined,
                                  size: 20,
                                ),
                                onPressed: () => setState(
                                  () => _verPassword = !_verPassword,
                                ),
                              ),
                            ),
                            validator: (v) {
                              final texto = v ?? '';
                              if (texto.isEmpty) {
                                return 'Elige una contraseña.';
                              }
                              if (texto.length < 8) {
                                return 'Necesita al menos 8 caracteres.';
                              }
                              return null;
                            },
                          ),

                          const TituloSeccion('Privacidad'),
                          _TarjetaAviso(
                            aviso: _aviso!,
                            onVerCompleto: _verAvisoCompleto,
                          ),
                          const SizedBox(height: Esp.sm),

                          CheckboxListTile(
                            value: _acepta,
                            onChanged: ocupado
                                ? null
                                : (v) => setState(() => _acepta = v ?? false),
                            controlAffinity: ListTileControlAffinity.leading,
                            contentPadding: EdgeInsets.zero,
                            title: Text(
                              'Leí y acepto el aviso de privacidad '
                              'versión ${_aviso!.version}',
                              style: tema.textTheme.bodyMedium,
                            ),
                            subtitle: Text(
                              'Puedes retirar este consentimiento después, '
                              'sin perder la cuenta.',
                              style: tema.textTheme.bodySmall?.copyWith(
                                color: tema.colorScheme.onSurfaceVariant,
                              ),
                            ),
                          ),

                          if (_error != null) ...[
                            const SizedBox(height: Esp.sm),
                            Container(
                              padding: const EdgeInsets.all(Esp.sm + 4),
                              decoration: BoxDecoration(
                                color: tema.colorScheme.surfaceContainerHigh,
                                borderRadius: BorderRadius.circular(10),
                                border: Border(
                                  left: BorderSide(
                                    color: tema.colorScheme.error,
                                    width: 3,
                                  ),
                                ),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(
                                    Icons.error_outline,
                                    size: 17,
                                    color: tema.colorScheme.error,
                                  ),
                                  const SizedBox(width: Esp.sm),
                                  Expanded(
                                    child: Text(
                                      _error!,
                                      style: tema.textTheme.bodySmall,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],

                          const SizedBox(height: Esp.lg),
                          FilledButton(
                            onPressed: ocupado ? null : _registrar,
                            child: ocupado
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text('Crear mi cuenta'),
                          ),
                          const SizedBox(height: Esp.md),
                          const AvisoNoCausalidad(compacto: true),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
      ),
    );
  }
}

class _TarjetaAviso extends StatelessWidget {
  const _TarjetaAviso({required this.aviso, required this.onVerCompleto});

  final AvisoPrivacidad aviso;
  final VoidCallback onVerCompleto;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Esp.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.shield_outlined,
                  size: 18,
                  color: tema.colorScheme.primary,
                ),
                const SizedBox(width: Esp.sm),
                Expanded(
                  child: Text(aviso.titulo, style: tema.textTheme.titleSmall),
                ),
              ],
            ),
            const SizedBox(height: Esp.sm),
            Text(
              'Tus datos se usan solo para buscar patrones en tu propio '
              'diario. No se venden, no se comparten y nadie más los ve.',
              style: tema.textTheme.bodySmall?.copyWith(
                color: tema.colorScheme.onSurfaceVariant,
                height: 1.45,
              ),
            ),
            const SizedBox(height: Esp.sm),
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton(
                onPressed: onVerCompleto,
                style: TextButton.styleFrom(
                  padding: EdgeInsets.zero,
                  minimumSize: const Size(0, 36),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: const Text('Leer el aviso completo'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
