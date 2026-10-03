import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_cliente.dart';
import '../../core/tema.dart';
import '../../core/widgets.dart';
import '../../estado/estado_bitacora.dart';
import '../../modelos/bitacora.dart';

/// HU-06 (alta), HU-08 (edición) y HU-09 (eliminación) del episodio.
class FormEpisodio extends StatefulWidget {
  const FormEpisodio({super.key, this.existente});

  /// Null para un episodio nuevo.
  final Episodio? existente;

  @override
  State<FormEpisodio> createState() => _FormEpisodioState();
}

class _FormEpisodioState extends State<FormEpisodio> {
  late Episodio _ep;
  late final TextEditingController _observacion;
  bool _sigueEnCurso = false;
  bool _guardando = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _ep = widget.existente ?? Episodio.nuevo();
    _sigueEnCurso = _ep.enCurso;
    _observacion = TextEditingController(text: _ep.observacion);
  }

  @override
  void dispose() {
    _observacion.dispose();
    super.dispose();
  }

  bool get _esEdicion => widget.existente != null;

  Future<void> _elegirInicio() async {
    final ahora = DateTime.now();
    final fecha = await showDatePicker(
      context: context,
      initialDate: _ep.inicio,
      firstDate: ahora.subtract(const Duration(days: 365)),
      lastDate: ahora,
      helpText: '¿Qué día empezó?',
    );
    if (fecha == null || !mounted) return;

    final hora = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_ep.inicio),
      helpText: '¿A qué hora empezó?',
    );
    if (hora == null) return;

    var elegido = DateTime(
      fecha.year,
      fecha.month,
      fecha.day,
      hora.hour,
      hora.minute,
    );
    // El backend rechaza un inicio futuro; se corrige antes de enviarlo para
    // que el paciente no reciba un error por un desfase de minutos.
    if (elegido.isAfter(DateTime.now())) elegido = DateTime.now();

    setState(() => _ep = _ep.copiar(inicio: elegido));
  }

  Future<void> _guardar() async {
    setState(() {
      _guardando = true;
      _error = null;
    });

    final aEnviar = _ep.copiar(
      observacion: _observacion.text.trim(),
      limpiarDuracion: _sigueEnCurso,
    );

    final estado = context.read<EstadoBitacora>();
    try {
      await estado.servicio.guardarEpisodio(aEnviar);
      await estado.recargar();
      if (!mounted) return;
      avisar(
        context,
        _esEdicion ? 'Episodio actualizado' : 'Episodio guardado',
      );
      Navigator.pop(context, true);
    } on DioException catch (e) {
      if (mounted) setState(() => _error = _detalleDe(e));
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  String _detalleDe(DioException e) {
    final datos = e.response?.data;
    if (datos is Map) {
      for (final valor in datos.values) {
        if (valor is List && valor.isNotEmpty) return valor.first.toString();
        if (valor is String) return valor;
      }
    }
    return mensajeDeError(e);
  }

  Future<void> _eliminar() async {
    final seguro = await confirmar(
      context,
      titulo: '¿Eliminar este episodio?',
      mensaje:
          'Se borra de forma permanente y deja de contar para el análisis.',
    );
    if (!seguro || !mounted) return;

    final estado = context.read<EstadoBitacora>();
    try {
      await estado.servicio.eliminarEpisodio(_ep.id!);
      await estado.recargar();
      if (!mounted) return;
      avisar(context, 'Episodio eliminado');
      Navigator.pop(context, true);
    } on DioException catch (e) {
      if (mounted) avisar(context, mensajeDeError(e), esError: true);
    }
  }

  /// Si marca vómitos, se activan las náuseas sola.
  ///
  /// El backend rechaza vómitos sin náuseas por coherencia clínica. Ajustarlo
  /// aquí evita que el paciente reciba un error por algo que el sistema puede
  /// deducir solo.
  void _cambiarVomitos(bool valor) {
    setState(() {
      _ep = _ep.copiar(vomitos: valor, nauseas: valor ? true : _ep.nauseas);
    });
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(_esEdicion ? 'Editar episodio' : 'Nuevo episodio'),
        actions: [
          if (_esEdicion)
            IconButton(
              onPressed: _guardando ? null : _eliminar,
              icon: const Icon(Icons.delete_outline),
              tooltip: 'Eliminar episodio',
            ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(Esp.md, Esp.md, Esp.md, Esp.xxl),
        children: [
          const TituloSeccion('Cuándo empezó'),
          Card(
            child: ListTile(
              leading: const Icon(Icons.event_outlined, size: 20),
              title: const Text('Inicio'),
              subtitle: Text(_fechaHoraLegible(_ep.inicio)),
              trailing: const Icon(Icons.chevron_right, size: 20),
              onTap: _guardando ? null : _elegirInicio,
            ),
          ),

          const TituloSeccion('Cuánto duró'),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  value: _sigueEnCurso,
                  onChanged: _guardando
                      ? null
                      : (v) => setState(() => _sigueEnCurso = v),
                  title: const Text('Todavía me duele'),
                  subtitle: const Text(
                    'Puedes volver después y completar la duración.',
                  ),
                ),
                if (!_sigueEnCurso) ...[
                  const Divider(height: 1),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(
                      Esp.md,
                      Esp.sm,
                      Esp.md,
                      Esp.xs,
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                'Duración',
                                style: tema.textTheme.bodyLarge,
                              ),
                            ),
                            Text(
                              _duracionLegible(_ep.duracionMin ?? 0),
                              style: tema.textTheme.bodyMedium?.copyWith(
                                color: tema.colorScheme.primary,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                        Slider(
                          value: ((_ep.duracionMin ?? 60) / 15)
                              .clamp(1, 96)
                              .toDouble(),
                          min: 1,
                          max: 96,
                          divisions: 95,
                          label: _duracionLegible(_ep.duracionMin ?? 60),
                          onChanged: (v) => setState(
                            () =>
                                _ep = _ep.copiar(duracionMin: (v.round() * 15)),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),

          const TituloSeccion(
            'Intensidad',
            ayuda: 'Escala EVA, de 1 (muy leve) a 10 (el peor imaginable).',
          ),
          _SelectorEva(
            valor: _ep.intensidad,
            onCambio: (v) => setState(() => _ep = _ep.copiar(intensidad: v)),
          ),

          const TituloSeccion('Síntomas que acompañaron'),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  value: _ep.nauseas,
                  // Con vómitos marcados, las náuseas quedan fijas.
                  onChanged: _guardando || _ep.vomitos
                      ? null
                      : (v) => setState(() => _ep = _ep.copiar(nauseas: v)),
                  title: const Text('Náuseas'),
                  subtitle: _ep.vomitos
                      ? const Text('Implícitas si hubo vómitos.')
                      : null,
                ),
                const Divider(height: 1),
                SwitchListTile(
                  value: _ep.vomitos,
                  onChanged: _guardando ? null : _cambiarVomitos,
                  title: const Text('Vómitos'),
                ),
                const Divider(height: 1),
                SwitchListTile(
                  value: _ep.sensibilidadLuz,
                  onChanged: _guardando
                      ? null
                      : (v) => setState(
                          () => _ep = _ep.copiar(sensibilidadLuz: v),
                        ),
                  title: const Text('Sensibilidad a la luz'),
                ),
                const Divider(height: 1),
                SwitchListTile(
                  value: _ep.sensibilidadSonido,
                  onChanged: _guardando
                      ? null
                      : (v) => setState(
                          () => _ep = _ep.copiar(sensibilidadSonido: v),
                        ),
                  title: const Text('Sensibilidad al sonido'),
                ),
              ],
            ),
          ),

          const TituloSeccion('Observación'),
          TextField(
            controller: _observacion,
            maxLines: 4,
            maxLength: 500,
            enabled: !_guardando,
            textCapitalization: TextCapitalization.sentences,
            decoration: const InputDecoration(
              hintText:
                  'Algo que quieras recordar: dónde estabas, qué hiciste '
                  'antes, qué te alivió…',
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
                  left: BorderSide(color: tema.colorScheme.error, width: 3),
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
                    child: Text(_error!, style: tema.textTheme.bodySmall),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
      bottomNavigationBar: Container(
        padding: EdgeInsets.fromLTRB(
          Esp.md,
          Esp.sm,
          Esp.md,
          MediaQuery.of(context).padding.bottom + Esp.sm,
        ),
        decoration: BoxDecoration(
          color: tema.colorScheme.surfaceContainerLow,
          border: Border(top: BorderSide(color: tema.colorScheme.outline)),
        ),
        child: FilledButton(
          onPressed: _guardando ? null : _guardar,
          child: _guardando
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(_esEdicion ? 'Actualizar episodio' : 'Guardar episodio'),
        ),
      ),
    );
  }
}

String _duracionLegible(int minutos) {
  final h = minutos ~/ 60;
  final m = minutos % 60;
  if (h == 0) return '$m min';
  if (m == 0) return '$h h';
  return '$h h $m min';
}

String _fechaHoraLegible(DateTime d) {
  final hoy = DateTime.now();
  final esHoy = d.year == hoy.year && d.month == hoy.month && d.day == hoy.day;
  final hh = d.hour.toString().padLeft(2, '0');
  final mm = d.minute.toString().padLeft(2, '0');
  if (esHoy) return 'Hoy a las $hh:$mm';
  return '${d.day}/${d.month}/${d.year} a las $hh:$mm';
}

/// Selector de intensidad EVA 1-10.
///
/// Usa la rampa cálida, nunca el color de marca: así el botón principal y «el
/// dolor fue intenso» nunca se confunden visualmente.
class _SelectorEva extends StatelessWidget {
  const _SelectorEva({required this.valor, required this.onCambio});

  final int valor;
  final ValueChanged<int> onCambio;

  static const _descripciones = {
    1: 'Apenas lo noto',
    2: 'Muy leve',
    3: 'Leve',
    4: 'Molesto',
    5: 'Moderado',
    6: 'Incómodo',
    7: 'Intenso',
    8: 'Muy intenso',
    9: 'Insoportable',
    10: 'El peor imaginable',
  };

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final color = Paleta.porIntensidad(valor);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Esp.md),
        child: Column(
          children: [
            Row(
              children: [
                InsigniaEva(valor, grande: true),
                const SizedBox(width: Esp.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _descripciones[valor] ?? '',
                        style: tema.textTheme.titleSmall?.copyWith(
                          color: color,
                        ),
                      ),
                      Text(
                        'Intensidad $valor de 10',
                        style: tema.textTheme.bodySmall?.copyWith(
                          color: tema.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: Esp.md),
            Row(
              children: [
                for (var n = 1; n <= 10; n++)
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 1.5),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(6),
                        onTap: () => onCambio(n),
                        child: Container(
                          height: 38,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: n <= valor
                                ? Paleta.porIntensidad(
                                    n,
                                  ).withValues(alpha: 0.85)
                                : tema.colorScheme.surfaceContainerHigh,
                            borderRadius: BorderRadius.circular(6),
                            border: n == valor
                                ? Border.all(
                                    color: tema.colorScheme.onSurface,
                                    width: 1.5,
                                  )
                                : null,
                          ),
                          child: Text(
                            '$n',
                            style: TextStyle(
                              fontSize: 11.5,
                              fontWeight: FontWeight.w700,
                              color: n <= valor
                                  ? const Color(0xFF14181A)
                                  : tema.colorScheme.onSurfaceVariant,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
