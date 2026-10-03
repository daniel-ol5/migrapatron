import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/tema.dart';
import '../../core/widgets.dart';
import '../../estado/estado_bitacora.dart';
import '../../modelos/bitacora.dart';
import '../bitacora/form_bitacora.dart';
import '../episodios/form_episodio.dart';

/// HU-07. Historial propio ordenado cronológicamente.
///
/// Muestra también los días SIN registrar, y eso es deliberado: ver los huecos
/// es parte del valor. El paciente necesita saber qué le falta para que el
/// análisis tenga datos suficientes, no solo qué ya hizo.
class PantallaHistorial extends StatefulWidget {
  const PantallaHistorial({super.key});

  @override
  State<PantallaHistorial> createState() => _PantallaHistorialState();
}

class _PantallaHistorialState extends State<PantallaHistorial> {
  int _dias = 30;
  bool _soloConRegistro = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final estado = context.read<EstadoBitacora>();
      if (estado.historial == null) estado.recargar(dias: _dias);
    });
  }

  @override
  Widget build(BuildContext context) {
    final estado = context.watch<EstadoBitacora>();
    final tema = Theme.of(context);

    var dias = estado.diasVisibles;
    if (_soloConRegistro) {
      dias = dias.where((d) => d.tieneBitacora || d.tuvoEpisodio).toList();
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Historial'),
        actions: [
          IconButton(
            icon: Icon(
              _soloConRegistro ? Icons.filter_alt : Icons.filter_alt_outlined,
              size: 21,
            ),
            tooltip: _soloConRegistro
                ? 'Mostrar todos los días'
                : 'Ocultar días sin registrar',
            onPressed: () =>
                setState(() => _soloConRegistro = !_soloConRegistro),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(Esp.md, Esp.sm, Esp.md, Esp.sm),
            child: SegmentedButton<int>(
              segments: const [
                ButtonSegment(value: 7, label: Text('7 días')),
                ButtonSegment(value: 30, label: Text('30 días')),
                ButtonSegment(value: 90, label: Text('90 días')),
              ],
              selected: {_dias},
              showSelectedIcon: false,
              onSelectionChanged: (seleccion) {
                setState(() => _dias = seleccion.first);
                context.read<EstadoBitacora>().recargar(dias: _dias);
              },
            ),
          ),

          if (estado.historial != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(Esp.md, 0, Esp.md, Esp.sm),
              child: Row(
                children: [
                  _Pastilla(
                    icono: Icons.event_available_outlined,
                    texto:
                        '${estado.historial!.bitacorasCompletas} días completos',
                  ),
                  const SizedBox(width: Esp.sm),
                  _Pastilla(
                    icono: Icons.bolt_outlined,
                    texto: '${estado.historial!.totalEpisodios} episodios',
                  ),
                ],
              ),
            ),

          const Divider(height: 1),

          Expanded(
            child: estado.cargando && estado.historial == null
                ? const Center(child: CircularProgressIndicator())
                : estado.error != null
                ? EstadoVacio(
                    icono: Icons.cloud_off_outlined,
                    titulo: 'No se pudo cargar el historial',
                    detalle: estado.error,
                    accion: OutlinedButton(
                      onPressed: () =>
                          context.read<EstadoBitacora>().recargar(dias: _dias),
                      child: const Text('Reintentar'),
                    ),
                  )
                : dias.isEmpty
                ? const EstadoVacio(
                    icono: Icons.calendar_today_outlined,
                    titulo: 'Nada registrado en este periodo',
                    detalle: 'Registra tu día desde la pantalla de inicio.',
                  )
                : RefreshIndicator(
                    onRefresh: () =>
                        context.read<EstadoBitacora>().recargar(dias: _dias),
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(
                        Esp.md,
                        Esp.sm,
                        Esp.md,
                        Esp.xxl,
                      ),
                      itemCount: dias.length,
                      separatorBuilder: (_, _) =>
                          const SizedBox(height: Esp.sm),
                      itemBuilder: (_, i) => _FilaDia(dia: dias[i]),
                    ),
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const FormEpisodio()),
        ),
        backgroundColor: tema.colorScheme.primary,
        foregroundColor: tema.colorScheme.onPrimary,
        tooltip: 'Registrar un episodio',
        child: const Icon(Icons.bolt_outlined),
      ),
    );
  }
}

class _Pastilla extends StatelessWidget {
  const _Pastilla({required this.icono, required this.texto});

  final IconData icono;
  final String texto;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: Esp.sm + 2, vertical: 5),
      decoration: BoxDecoration(
        color: tema.colorScheme.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: tema.colorScheme.outline),
      ),
      child: Row(
        children: [
          Icon(icono, size: 14, color: tema.colorScheme.onSurfaceVariant),
          const SizedBox(width: Esp.xs + 2),
          Text(texto, style: tema.textTheme.bodySmall?.copyWith(fontSize: 12)),
        ],
      ),
    );
  }
}

class _FilaDia extends StatelessWidget {
  const _FilaDia({required this.dia});

  final DiaHistorial dia;

  static const _diasSemana = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'];

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final vacio = !dia.tieneBitacora && !dia.tuvoEpisodio;

    return Opacity(
      // Los días sin nada se atenúan, pero siguen visibles: el hueco es
      // información, no basura que haya que esconder.
      opacity: vacio ? 0.55 : 1,
      child: Card(
        child: Column(
          children: [
            InkWell(
              borderRadius: BorderRadius.vertical(
                top: const Radius.circular(14),
                bottom: Radius.circular(dia.tuvoEpisodio ? 0 : 14),
              ),
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => FormBitacora(fecha: dia.fecha),
                ),
              ),
              child: Padding(
                padding: const EdgeInsets.all(Esp.md),
                child: Row(
                  children: [
                    SizedBox(
                      width: 42,
                      child: Column(
                        children: [
                          Text(
                            '${dia.fecha.day}',
                            style: tema.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w700,
                              fontFeatures: const [
                                FontFeature.tabularFigures(),
                              ],
                            ),
                          ),
                          Text(
                            _diasSemana[dia.fecha.weekday - 1],
                            style: tema.textTheme.bodySmall?.copyWith(
                              color: tema.colorScheme.onSurfaceVariant,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: Esp.sm),
                    Container(
                      width: 1,
                      height: 32,
                      color: tema.colorScheme.outline,
                    ),
                    const SizedBox(width: Esp.md),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _estadoDelDia(),
                            style: tema.textTheme.bodyMedium?.copyWith(
                              color: dia.tieneBitacora
                                  ? tema.colorScheme.onSurface
                                  : tema.colorScheme.onSurfaceVariant,
                            ),
                          ),
                          if (dia.medicacionRescate) ...[
                            const SizedBox(height: 3),
                            Text(
                              'Medicación de rescate',
                              style: tema.textTheme.bodySmall?.copyWith(
                                color: Paleta.aviso,
                                fontSize: 11.5,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    if (dia.tieneBitacora)
                      Icon(
                        dia.bitacoraCompleta
                            ? Icons.check_circle_outline
                            : Icons.pending_outlined,
                        size: 18,
                        color: dia.bitacoraCompleta
                            ? Paleta.exito
                            : Paleta.aviso,
                      )
                    else
                      Icon(
                        Icons.add_circle_outline,
                        size: 18,
                        color: tema.colorScheme.onSurfaceVariant,
                      ),
                  ],
                ),
              ),
            ),

            if (dia.tuvoEpisodio) ...[
              const Divider(height: 1),
              for (final ep in dia.episodios)
                ListTile(
                  dense: true,
                  leading: InsigniaEva(ep.intensidad),
                  title: Text(
                    ep.duracionLegible,
                    style: tema.textTheme.bodyMedium,
                  ),
                  subtitle: ep.sintomasPresentes.isEmpty
                      ? null
                      : Text(
                          ep.sintomasPresentes.join(', '),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: tema.textTheme.bodySmall?.copyWith(
                            color: tema.colorScheme.onSurfaceVariant,
                          ),
                        ),
                  trailing: const Icon(Icons.chevron_right, size: 19),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => FormEpisodio(existente: ep),
                    ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  String _estadoDelDia() {
    if (!dia.tieneBitacora) return 'Sin registrar';
    if (!dia.bitacoraCompleta) return 'Registro incompleto';
    return 'Día completo';
  }
}
