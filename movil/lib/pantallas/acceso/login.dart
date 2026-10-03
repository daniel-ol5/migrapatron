import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/tema.dart';
import '../../estado/estado_sesion.dart';
import 'registro.dart';

/// HU-02. Inicio de sesión.
class PantallaLogin extends StatefulWidget {
  const PantallaLogin({super.key});

  @override
  State<PantallaLogin> createState() => _PantallaLoginState();
}

class _PantallaLoginState extends State<PantallaLogin> {
  final _formulario = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _verPassword = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _ingresar() async {
    setState(() => _error = null);
    if (!_formulario.currentState!.validate()) return;

    final mensaje = await context.read<EstadoSesion>().ingresar(
      email: _email.text,
      password: _password.text,
    );
    if (mensaje != null && mounted) setState(() => _error = mensaje);
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final ocupado = context.watch<EstadoSesion>().ocupado;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(Esp.lg),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _formulario,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const _Marca(),
                    const SizedBox(height: Esp.xl),

                    Text('Entrar', style: tema.textTheme.headlineSmall),
                    const SizedBox(height: Esp.xs),
                    Text(
                      'Tu diario es privado y solo tú lo ves.',
                      style: tema.textTheme.bodyMedium?.copyWith(
                        color: tema.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: Esp.lg),

                    TextFormField(
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      autofillHints: const [AutofillHints.email],
                      enabled: !ocupado,
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        prefixIcon: Icon(Icons.mail_outline, size: 20),
                      ),
                      validator: (v) {
                        final texto = (v ?? '').trim();
                        if (texto.isEmpty) return 'Escribe tu email.';
                        if (!texto.contains('@') || !texto.contains('.')) {
                          return 'Ese email no parece válido.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: Esp.md),

                    TextFormField(
                      controller: _password,
                      obscureText: !_verPassword,
                      textInputAction: TextInputAction.done,
                      autofillHints: const [AutofillHints.password],
                      enabled: !ocupado,
                      onFieldSubmitted: (_) => ocupado ? null : _ingresar(),
                      decoration: InputDecoration(
                        labelText: 'Contraseña',
                        prefixIcon: const Icon(Icons.lock_outline, size: 20),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _verPassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                            size: 20,
                          ),
                          onPressed: () =>
                              setState(() => _verPassword = !_verPassword),
                          tooltip: _verPassword ? 'Ocultar' : 'Mostrar',
                        ),
                      ),
                      validator: (v) =>
                          (v ?? '').isEmpty ? 'Escribe tu contraseña.' : null,
                    ),

                    if (_error != null) ...[
                      const SizedBox(height: Esp.md),
                      _Error(_error!),
                    ],

                    const SizedBox(height: Esp.lg),
                    FilledButton(
                      onPressed: ocupado ? null : _ingresar,
                      child: ocupado
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Entrar'),
                    ),
                    const SizedBox(height: Esp.sm),
                    TextButton(
                      onPressed: ocupado
                          ? null
                          : () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => const PantallaRegistro(),
                              ),
                            ),
                      child: const Text('No tengo cuenta, quiero crear una'),
                    ),
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

class _Marca extends StatelessWidget {
  const _Marca();

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Column(
      children: [
        Container(
          width: 58,
          height: 58,
          decoration: BoxDecoration(
            color: tema.colorScheme.surfaceContainerHigh,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: tema.colorScheme.outline),
          ),
          child: Icon(
            Icons.insights_outlined,
            size: 28,
            color: tema.colorScheme.primary,
          ),
        ),
        const SizedBox(height: Esp.md),
        Text(
          'MigraPatrón',
          style: tema.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w700,
            letterSpacing: -0.4,
          ),
        ),
        Text(
          'Tu diario de migraña',
          style: tema.textTheme.bodySmall?.copyWith(
            color: tema.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}

class _Error extends StatelessWidget {
  const _Error(this.mensaje);

  final String mensaje;

  @override
  Widget build(BuildContext context) {
    final esquema = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(Esp.sm + 4),
      decoration: BoxDecoration(
        color: esquema.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(10),
        border: Border(left: BorderSide(color: esquema.error, width: 3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.error_outline, size: 17, color: esquema.error),
          const SizedBox(width: Esp.sm),
          Expanded(
            child: Text(
              mensaje,
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: esquema.onSurface),
            ),
          ),
        ],
      ),
    );
  }
}
