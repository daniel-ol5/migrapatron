import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_cliente.dart';
import '../../core/tema.dart';
import '../../core/widgets.dart';
import '../../estado/estado_bitacora.dart';
import '../../estado/estado_sesion.dart';
import '../../modelos/bitacora.dart';

/// HU-05 (alta), HU-08 (edición) y HU-09 (eliminación) de la bitácora.
///
/// Al abrirse busca si ese día ya tiene registro. Si existe entra en modo
/// edición, porque la unicidad (usuario, fecha) haría fallar un alta. El
/// paciente nunca ve el error: ve el formulario con sus valores cargados.
class FormBitacora extends StatefulWidget {
  const FormBitacora({super.key, required this.fecha});

  final DateTime fecha;

  @override
  State<FormBitacora> createState() => _FormBitacoraState();
}

class _FormBitacoraState extends State<FormBitacora> {
  RegistroDiario? _registro;
  bool _cargando = true;
  bool _guardando = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });

    final servicio = context.read<EstadoBitacora>().servicio;
    final horaPreferida =
        context.read<EstadoSesion>().usuario?.perfil.horaCortePreferida ??
        '22:00:00';

    try {
      final existente = await servicio.bitacoraDe(widget.fecha);
      if (!mounted) return;
      setState(() {
        _registro =
            existente ??
            RegistroDiario.vacio(
              fecha: widget.fecha,
              horaCorte: horaPreferida.substring(0, 5),
            );
      });
    } on DioException catch (e) {
      if (mounted) setState(() => _error = mensajeDeError(e));
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  void _actualizar(RegistroDiario nuevo) => setState(() => _registro = nuevo);

  Future<void> _guardar() async {
    setState(() {
      _guardando = true;
      _error = null;
    });

    // Se toma el estado antes del await: despues de un await el context puede
    // haber quedado desmontado.
    final estado = context.read<EstadoBitacora>();
    try {
      await estado.servicio.guardarBitacora(_registro!);
      await estado.recargar();
      if (!mounted) return;
      avisar(context, 'Día guardado');
      Navigator.pop(context, true);
    } on DioException catch (e) {
      if (mounted) setState(() => _error = _detalleDe(e));
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  /// Saca el mensaje del campo que el backend rechazó, en vez de mostrar un
  /// genérico. Si el backend dice «ya registraste este día», eso es mucho más
  /// útil que «ocurrió un error».
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
      titulo: '¿Eliminar este día?',
      mensaje:
          'Se borran los factores que registraste. '
          'Los episodios de ese día se conservan.',
    );
    if (!seguro || !mounted) return;

    final estado = context.read<EstadoBitacora>();
    try {
      await estado.servicio.eliminarBitacora(_registro!.id!);
      await estado.recargar();
      if (!mounted) return;
      avisar(context, 'Día eliminado');
      Navigator.pop(context, true);
    } on DioException catch (e) {
      if (mounted) avisar(context, mensajeDeError(e), esError: true);
    }
  }

  Future<void> _elegirHoraCorte() async {
    final partes = _registro!.horaCorte.split(':');
    final elegida = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(
        hour: int.tryParse(partes[0]) ?? 22,
        minute: int.tryParse(partes.length > 1 ? partes[1] : '0') ?? 0,
      ),
      helpText: 'Hora en que cierras el día',
    );
    if (elegida == null) return;
    final hh = elegida.hour.toString().padLeft(2, '0');
    final mm = elegida.minute.toString().padLeft(2, '0');
    _actualizar(_registro!.copiar(horaCorte: '$hh:$mm'));
  }

  @override
  Widget build(BuildContext context) {
    final esEdicion = _registro?.esNuevo == false;

    return Scaffold(
      appBar: AppBar(
        title: Text(esEdicion ? 'Editar el día' : 'Registrar el día'),
        actions: [
          if (esEdicion)
            IconButton(
              onPressed: _guardando ? null : _eliminar,
              icon: const Icon(Icons.delete_outline),
              tooltip: 'Eliminar este día',
            ),
        ],
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _registro == null
          ? EstadoVacio(
              icono: Icons.cloud_off_outlined,
              titulo: 'No se pudo cargar el día',
              detalle: _error,
              accion: OutlinedButton(
                onPressed: _cargar,
                child: const Text('Reintentar'),
              ),
            )
          : _contenido(),
      bottomNavigationBar: _registro == null ? null : _barraGuardar(),
    );
  }

  Widget _contenido() {
    final r = _registro!;
    final tema = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.fromLTRB(Esp.md, Esp.md, Esp.md, Esp.xxl),
      children: [
        _Cabecera(
          fecha: r.fecha,
          completos: r.factoresCompletos,
          total: RegistroDiario.totalFactores,
        ),

        const TituloSeccion(
          'Hora de corte',
          ayuda:
              'A qué hora cierras tu día. El análisis la usa para saber qué '
              'factores ocurrieron antes de un episodio.',
        ),
        Card(
          child: ListTile(
            leading: const Icon(Icons.schedule_outlined, size: 20),
            title: const Text('Cierro mi día a las'),
            trailing: Text(
              r.horaCorte,
              style: tema.textTheme.titleMedium?.copyWith(
                color: tema.colorScheme.primary,
                fontWeight: FontWeight.w600,
              ),
            ),
            onTap: _guardando ? null : _elegirHoraCorte,
          ),
        ),

        const TituloSeccion('Sueño y alimentación'),
        _CampoDecimal(
          etiqueta: 'Horas de sueño',
          valor: r.horasSueno,
          maximo: 14,
          sufijo: 'h',
          decimales: true,
          onCambio: (v) => _actualizar(r.copiar(horasSueno: v)),
        ),
        _CampoOpciones(
          etiqueta: 'Hidratación',
          opciones: RegistroDiario.opcionesHidratacion,
          valor: r.hidratacion,
          onCambio: (v) => _actualizar(r.copiar(hidratacion: v)),
        ),
        _CampoEntero(
          etiqueta: 'Comidas que te saltaste',
          valor: r.comidaOmitida,
          maximo: 3,
          onCambio: (v) => _actualizar(r.copiar(comidaOmitida: v)),
        ),
        _CampoEntero(
          etiqueta: 'Tazas de café o té',
          valor: r.cafeinaTazas,
          maximo: 10,
          onCambio: (v) => _actualizar(r.copiar(cafeinaTazas: v)),
        ),

        const TituloSeccion('Estrés y actividad'),
        _CampoEscala(
          etiqueta: 'Estrés percibido',
          valor: r.estres,
          minimo: 1,
          maximo: 5,
          etiquetasExtremos: const ('Tranquilo', 'Muy estresado'),
          onCambio: (v) => _actualizar(r.copiar(estres: v)),
        ),
        _CampoDecimal(
          etiqueta: 'Horas frente a pantallas',
          valor: r.horasPantalla,
          maximo: 16,
          sufijo: 'h',
          decimales: true,
          onCambio: (v) => _actualizar(r.copiar(horasPantalla: v)),
        ),
        _CampoDecimal(
          etiqueta: 'Minutos de actividad física',
          valor: r.minutosActividad?.toDouble(),
          maximo: 180,
          paso: 5,
          sufijo: 'min',
          onCambio: (v) => _actualizar(r.copiar(minutosActividad: v?.round())),
        ),

        const TituloSeccion('Contexto clínico'),
        if (context.read<EstadoSesion>().usuario!.perfil.registraCicloMenstrual)
          _CampoOpciones(
            etiqueta: 'Contexto menstrual',
            opciones: RegistroDiario.opcionesCiclo,
            valor: r.contextoMenstrual,
            onCambio: (v) => _actualizar(r.copiar(contextoMenstrual: v)),
          ),
        Card(
          child: Column(
            children: [
              SwitchListTile(
                value: r.medicacionRescate,
                onChanged: _guardando
                    ? null
                    : (v) => _actualizar(r.copiar(medicacionRescate: v)),
                title: const Text('Tomé medicación de rescate'),
                subtitle: const Text(
                  'Tu médico necesita ver con qué frecuencia la usas.',
                ),
              ),
              const Divider(height: 1),
              SwitchListTile(
                value: r.sensacionesPremonitorias,
                onChanged: _guardando
                    ? null
                    : (v) => _actualizar(r.copiar(sensacionesPremonitorias: v)),
                title: const Text('Tuve sensaciones premonitorias'),
                subtitle: const Text(
                  'Bostezos, antojos, irritabilidad, cuello tenso.',
                ),
              ),
            ],
          ),
        ),

        if (_error != null) ...[
          const SizedBox(height: Esp.md),
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
                Expanded(child: Text(_error!, style: tema.textTheme.bodySmall)),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _barraGuardar() {
    final tema = Theme.of(context);
    final r = _registro!;
    final faltan = RegistroDiario.totalFactores - r.factoresCompletos;

    return Container(
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
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (faltan > 0)
            Padding(
              padding: const EdgeInsets.only(bottom: Esp.sm),
              child: Text(
                faltan == 1
                    ? 'Falta 1 factor para que el día cuente en el análisis.'
                    : 'Faltan $faltan factores para que el día cuente en el '
                          'análisis.',
                textAlign: TextAlign.center,
                style: tema.textTheme.bodySmall?.copyWith(
                  color: tema.colorScheme.onSurfaceVariant,
                ),
              ),
            ),
          FilledButton(
            onPressed: _guardando ? null : _guardar,
            child: _guardando
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(r.esNuevo ? 'Guardar el día' : 'Actualizar'),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------- cabecera
class _Cabecera extends StatelessWidget {
  const _Cabecera({
    required this.fecha,
    required this.completos,
    required this.total,
  });

  final DateTime fecha;
  final int completos;
  final int total;

  static const _meses = [
    'enero',
    'febrero',
    'marzo',
    'abril',
    'mayo',
    'junio',
    'julio',
    'agosto',
    'septiembre',
    'octubre',
    'noviembre',
    'diciembre',
  ];

  bool get _esHoy {
    final hoy = DateTime.now();
    return fecha.year == hoy.year &&
        fecha.month == hoy.month &&
        fecha.day == hoy.day;
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Esp.md),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _esHoy
                        ? 'Hoy'
                        : '${fecha.day} de ${_meses[fecha.month - 1]}',
                    style: tema.textTheme.titleMedium,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '$completos de $total factores',
                    style: tema.textTheme.bodySmall?.copyWith(
                      color: tema.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(
              width: 40,
              height: 40,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  CircularProgressIndicator(
                    value: completos / total,
                    strokeWidth: 3.5,
                    backgroundColor: tema.colorScheme.outline,
                  ),
                  if (completos == total)
                    Icon(Icons.check, size: 18, color: Paleta.exito),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ------------------------------------------------------------ campos reusables
class _CampoDecimal extends StatelessWidget {
  const _CampoDecimal({
    required this.etiqueta,
    required this.valor,
    required this.maximo,
    required this.onCambio,
    this.sufijo = '',
    this.paso = 1,
    this.decimales = false,
  });

  final String etiqueta;
  final double? valor;
  final double maximo;
  final String sufijo;
  final double paso;
  final bool decimales;
  final ValueChanged<double?> onCambio;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final sinDato = valor == null;
    final texto = sinDato
        ? 'Sin registrar'
        : decimales
        ? '${valor!.toStringAsFixed(1)} $sufijo'
        : '${valor!.round()} $sufijo';

    return Card(
      margin: const EdgeInsets.only(bottom: Esp.sm),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(Esp.md, Esp.sm + 4, Esp.md, Esp.xs),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(etiqueta, style: tema.textTheme.bodyLarge),
                ),
                Text(
                  texto,
                  style: tema.textTheme.bodyMedium?.copyWith(
                    color: sinDato
                        ? tema.colorScheme.onSurfaceVariant
                        : tema.colorScheme.primary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (!sinDato)
                  IconButton(
                    icon: const Icon(Icons.backspace_outlined, size: 17),
                    onPressed: () => onCambio(null),
                    tooltip: 'Borrar este dato',
                    visualDensity: VisualDensity.compact,
                  ),
              ],
            ),
            Slider(
              value: (valor ?? 0).clamp(0, maximo),
              max: maximo,
              divisions: (maximo / paso).round(),
              onChanged: onCambio,
            ),
          ],
        ),
      ),
    );
  }
}

class _CampoEntero extends StatelessWidget {
  const _CampoEntero({
    required this.etiqueta,
    required this.valor,
    required this.maximo,
    required this.onCambio,
  });

  final String etiqueta;
  final int? valor;
  final int maximo;
  final ValueChanged<int?> onCambio;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: Esp.sm),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: Esp.md,
          vertical: Esp.sm,
        ),
        child: Row(
          children: [
            Expanded(child: Text(etiqueta, style: tema.textTheme.bodyLarge)),
            IconButton(
              icon: const Icon(Icons.remove_circle_outline, size: 22),
              onPressed: (valor ?? 0) <= 0
                  ? null
                  : () => onCambio(valor! - 1 < 0 ? null : valor! - 1),
            ),
            SizedBox(
              width: 34,
              child: Text(
                valor?.toString() ?? '–',
                textAlign: TextAlign.center,
                style: tema.textTheme.titleMedium?.copyWith(
                  color: valor == null
                      ? tema.colorScheme.onSurfaceVariant
                      : tema.colorScheme.primary,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.add_circle_outline, size: 22),
              onPressed: (valor ?? -1) >= maximo
                  ? null
                  : () => onCambio((valor ?? -1) + 1),
            ),
          ],
        ),
      ),
    );
  }
}

class _CampoEscala extends StatelessWidget {
  const _CampoEscala({
    required this.etiqueta,
    required this.valor,
    required this.minimo,
    required this.maximo,
    required this.onCambio,
    this.etiquetasExtremos,
  });

  final String etiqueta;
  final int? valor;
  final int minimo;
  final int maximo;
  final (String, String)? etiquetasExtremos;
  final ValueChanged<int?> onCambio;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: Esp.sm),
      child: Padding(
        padding: const EdgeInsets.all(Esp.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(etiqueta, style: tema.textTheme.bodyLarge),
            const SizedBox(height: Esp.sm + 2),
            Row(
              children: [
                for (var n = minimo; n <= maximo; n++)
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 3),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(8),
                        onTap: () => onCambio(valor == n ? null : n),
                        child: Container(
                          height: 42,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: valor == n
                                ? tema.colorScheme.primary
                                : tema.colorScheme.surfaceContainerHigh,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: valor == n
                                  ? tema.colorScheme.primary
                                  : tema.colorScheme.outline,
                            ),
                          ),
                          child: Text(
                            '$n',
                            style: TextStyle(
                              color: valor == n
                                  ? tema.colorScheme.onPrimary
                                  : tema.colorScheme.onSurfaceVariant,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            if (etiquetasExtremos != null) ...[
              const SizedBox(height: Esp.xs + 2),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    etiquetasExtremos!.$1,
                    style: tema.textTheme.bodySmall?.copyWith(
                      color: tema.colorScheme.onSurfaceVariant,
                      fontSize: 11.5,
                    ),
                  ),
                  Text(
                    etiquetasExtremos!.$2,
                    style: tema.textTheme.bodySmall?.copyWith(
                      color: tema.colorScheme.onSurfaceVariant,
                      fontSize: 11.5,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _CampoOpciones extends StatelessWidget {
  const _CampoOpciones({
    required this.etiqueta,
    required this.opciones,
    required this.valor,
    required this.onCambio,
  });

  final String etiqueta;
  final Map<String, String> opciones;
  final String valor;
  final ValueChanged<String> onCambio;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: Esp.sm),
      child: Padding(
        padding: const EdgeInsets.all(Esp.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(etiqueta, style: tema.textTheme.bodyLarge),
            const SizedBox(height: Esp.sm + 2),
            Wrap(
              spacing: Esp.sm,
              runSpacing: Esp.sm,
              children: [
                for (final entrada in opciones.entries)
                  ChoiceChip(
                    label: Text(entrada.value),
                    selected: valor == entrada.key,
                    onSelected: (elegido) =>
                        onCambio(elegido ? entrada.key : ''),
                    selectedColor: tema.colorScheme.primary,
                    labelStyle: TextStyle(
                      color: valor == entrada.key
                          ? tema.colorScheme.onPrimary
                          : tema.colorScheme.onSurface,
                      fontSize: 12.5,
                    ),
                    showCheckmark: false,
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
