import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/tema.dart';
import '../../core/widgets.dart';
import '../../estado/estado_bitacora.dart';
import '../../estado/estado_sesion.dart';
import '../../modelos/bitacora.dart';
import '../bitacora/form_bitacora.dart';
import '../episodios/form_episodio.dart';

/// Pantalla de inicio: el estado de hoy y el avance hacia el análisis.
class PantallaInicio extends StatefulWidget {
  const PantallaInicio({super.key});

  @override
  State<PantallaInicio> createState() => _PantallaInicioState();
}

class _PantallaInicioState extends State<PantallaInicio> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<EstadoBitacora>().recargar(dias: 30);
    });
  }

  Future<void> _abrirBitacoraDeHoy() async {
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => FormBitacora(fecha: DateTime.now())),
    );
  }

  Future<void> _abrirEpisodioNuevo() async {
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const FormEpisodio()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final sesion = context.watch<EstadoSesion>();
    final estado = context.watch<EstadoBitacora>();
    final tema = Theme.of(context);
    final usuario = sesion.usuario;

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => estado.recargar(),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(Esp.md, Esp.md, Esp.md, Esp.xxl),
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _saludo(),
                          style: tema.textTheme.bodyMedium?.copyWith(
                            color: tema.colorScheme.onSurfaceVariant,
                          ),
                        ),
                        Text(
                          usuario?.nombre ?? '',
                          style: tema.textTheme.headlineSmall,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: Esp.lg),

              _TarjetaHoy(
                registrado: estado.hoyRegistrado,
                completo: estado.hoy?.bitacoraCompleta ?? false,
                cargando: estado.cargando && estado.historial == null,
                onTocar: _abrirBitacoraDeHoy,
              ),
              const SizedBox(height: Esp.sm),

              OutlinedButton.icon(
                onPressed: _abrirEpisodioNuevo,
                icon: const Icon(Icons.bolt_outlined, size: 19),
                label: const Text('Registrar un episodio'),
              ),

              if (estado.historial != null) ...[
                const TituloSeccion('Avance hacia el análisis'),
                _TarjetaAvance(historial: estado.historial!),
              ],

              if (estado.episodiosRecientes.isNotEmpty) ...[
                const TituloSeccion('Últimos episodios'),
                Card(
                  child: Column(
                    children: [
                      for (final (i, ep)
                          in estado.episodiosRecientes.take(4).indexed) ...[
                        if (i > 0) const Divider(height: 1),
                        _FilaEpisodio(episodio: ep),
                      ],
                    ],
                  ),
                ),
              ],

              if (usuario != null && !usuario.consintioAnalisis) ...[
                const SizedBox(height: Esp.lg),
                _AvisoSinConsentimiento(),
              ],

              const SizedBox(height: Esp.lg),
              const AvisoNoCausalidad(compacto: true),
            ],
          ),
        ),
      ),
    );
  }

  String _saludo() {
    final hora = DateTime.now().hour;
    if (hora < 12) return 'Buenos días';
    if (hora < 19) return 'Buenas tardes';
    return 'Buenas noches';
  }
}

class _TarjetaHoy extends StatelessWidget {
  const _TarjetaHoy({
    required this.registrado,
    required this.completo,
    required this.cargando,
    required this.onTocar,
  });

  final bool registrado;
  final bool completo;
  final bool cargando;
  final VoidCallback onTocar;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);

    final (icono, titulo, detalle, color) = switch ((
      cargando,
      registrado,
      completo,
    )) {
      (true, _, _) => (
        Icons.sync,
        'Cargando tu día…',
        '',
        tema.colorScheme.onSurfaceVariant,
      ),
      (_, false, _) => (
        Icons.edit_calendar_outlined,
        'Hoy no has registrado',
        'Toma menos de un minuto.',
        tema.colorScheme.primary,
      ),
      (_, true, false) => (
        Icons.pending_outlined,
        'Tu día está incompleto',
        'Faltan factores para que cuente en el análisis.',
        Paleta.aviso,
      ),
      (_, true, true) => (
        Icons.check_circle_outline,
        'Día registrado',
        'Puedes editarlo si algo cambió.',
        Paleta.exito,
      ),
    };

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: cargando ? null : onTocar,
        child: Padding(
          padding: const EdgeInsets.all(Esp.md),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icono, color: color, size: 22),
              ),
              const SizedBox(width: Esp.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(titulo, style: tema.textTheme.titleSmall),
                    if (detalle.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        detalle,
                        style: tema.textTheme.bodySmall?.copyWith(
                          color: tema.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (!cargando)
                Icon(
                  Icons.chevron_right,
                  color: tema.colorScheme.onSurfaceVariant,
                ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Muestra cuánto falta para que M2 pueda analizar.
///
/// Los umbrales son los del documento: 20 bitácoras y 3 episodios. Mostrarlos
/// de forma explícita es lo que convierte «registra todos los días» en una meta
/// concreta.
class _TarjetaAvance extends StatelessWidget {
  const _TarjetaAvance({required this.historial});

  final Historial historial;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final listo = historial.puedeAnalizar;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Esp.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  listo ? Icons.verified_outlined : Icons.timelapse_outlined,
                  size: 18,
                  color: listo ? Paleta.exito : tema.colorScheme.primary,
                ),
                const SizedBox(width: Esp.sm),
                Expanded(
                  child: Text(
                    listo
                        ? 'Ya tienes datos suficientes'
                        : 'Todavía faltan datos',
                    style: tema.textTheme.titleSmall,
                  ),
                ),
              ],
            ),
            const SizedBox(height: Esp.md),

            _Barra(
              etiqueta: 'Días completos',
              actual: historial.bitacorasCompletas,
              meta: Historial.minimoBitacoras,
            ),
            const SizedBox(height: Esp.sm + 2),
            _Barra(
              etiqueta: 'Episodios',
              actual: historial.totalEpisodios,
              meta: Historial.minimoEpisodios,
            ),

            const SizedBox(height: Esp.md),
            Text(
              listo
                  ? 'El análisis de patrones estará disponible cuando se '
                        'implemente el módulo M2.'
                  : _queFalta(),
              style: tema.textTheme.bodySmall?.copyWith(
                color: tema.colorScheme.onSurfaceVariant,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _queFalta() {
    final partes = <String>[];
    if (historial.faltanBitacoras > 0) {
      partes.add(
        historial.faltanBitacoras == 1
            ? '1 día completo'
            : '${historial.faltanBitacoras} días completos',
      );
    }
    if (historial.faltanEpisodios > 0) {
      partes.add(
        historial.faltanEpisodios == 1
            ? '1 episodio'
            : '${historial.faltanEpisodios} episodios',
      );
    }
    return 'Faltan ${partes.join(' y ')} para poder buscar patrones.';
  }
}

class _Barra extends StatelessWidget {
  const _Barra({
    required this.etiqueta,
    required this.actual,
    required this.meta,
  });

  final String etiqueta;
  final int actual;
  final int meta;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final proporcion = (actual / meta).clamp(0.0, 1.0);
    final listo = actual >= meta;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                etiqueta,
                style: tema.textTheme.bodySmall?.copyWith(
                  color: tema.colorScheme.onSurfaceVariant,
                ),
              ),
            ),
            Text(
              '$actual / $meta',
              style: tema.textTheme.bodySmall?.copyWith(
                color: listo ? Paleta.exito : tema.colorScheme.onSurface,
                fontWeight: FontWeight.w600,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
          ],
        ),
        const SizedBox(height: Esp.xs + 1),
        ClipRRect(
          borderRadius: BorderRadius.circular(999),
          child: LinearProgressIndicator(
            value: proporcion,
            minHeight: 6,
            backgroundColor: tema.colorScheme.outline,
            valueColor: AlwaysStoppedAnimation(
              listo ? Paleta.exito : tema.colorScheme.primary,
            ),
          ),
        ),
      ],
    );
  }
}

class _FilaEpisodio extends StatelessWidget {
  const _FilaEpisodio({required this.episodio});

  final Episodio episodio;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final sintomas = episodio.sintomasPresentes.isNotEmpty
        ? episodio.sintomasPresentes
        : episodio.sintomasLocales;

    return ListTile(
      leading: InsigniaEva(episodio.intensidad),
      title: Text(
        _fechaCorta(episodio.inicio),
        style: tema.textTheme.bodyMedium,
      ),
      subtitle: Text(
        [
          episodio.duracionLegible,
          if (sintomas.isNotEmpty) sintomas.take(2).join(', '),
        ].join(' · '),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: tema.textTheme.bodySmall?.copyWith(
          color: tema.colorScheme.onSurfaceVariant,
        ),
      ),
      trailing: const Icon(Icons.chevron_right, size: 19),
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => FormEpisodio(existente: episodio)),
      ),
    );
  }
}

class _AvisoSinConsentimiento extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(Esp.md),
      decoration: BoxDecoration(
        color: tema.colorScheme.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(10),
        border: Border(left: BorderSide(color: Paleta.aviso, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'El análisis está desactivado',
            style: tema.textTheme.titleSmall,
          ),
          const SizedBox(height: Esp.xs),
          Text(
            'Retiraste tu consentimiento, así que no buscamos patrones en tus '
            'datos. Tus registros se conservan y puedes volver a activarlo '
            'desde tu perfil.',
            style: tema.textTheme.bodySmall?.copyWith(
              color: tema.colorScheme.onSurfaceVariant,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

String _fechaCorta(DateTime d) {
  final hoy = DateTime.now();
  final ayer = hoy.subtract(const Duration(days: 1));
  final hh = d.hour.toString().padLeft(2, '0');
  final mm = d.minute.toString().padLeft(2, '0');

  if (d.year == hoy.year && d.month == hoy.month && d.day == hoy.day) {
    return 'Hoy · $hh:$mm';
  }
  if (d.year == ayer.year && d.month == ayer.month && d.day == ayer.day) {
    return 'Ayer · $hh:$mm';
  }
  return '${d.day}/${d.month} · $hh:$mm';
}
