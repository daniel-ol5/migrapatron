import 'package:flutter/material.dart';

import 'config.dart';
import 'tema.dart';

/// El aviso de no causalidad.
///
/// No es letra chica legal: es un requisito funcional verificable. Acompaña a
/// todo lugar donde se muestren patrones o resultados del análisis.
class AvisoNoCausalidad extends StatelessWidget {
  const AvisoNoCausalidad({super.key, this.compacto = false});

  final bool compacto;

  @override
  Widget build(BuildContext context) {
    final esquema = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(compacto ? Esp.sm + 2 : Esp.md),
      decoration: BoxDecoration(
        color: esquema.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(10),
        border: Border(left: BorderSide(color: Paleta.aviso, width: 3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline, size: 17, color: Paleta.aviso),
          const SizedBox(width: Esp.sm),
          Expanded(
            child: Text(
              Config.avisoNoCausalidad,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: esquema.onSurfaceVariant,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Título de sección, para separar bloques dentro de un formulario largo.
class TituloSeccion extends StatelessWidget {
  const TituloSeccion(this.texto, {super.key, this.ayuda});

  final String texto;
  final String? ayuda;

  @override
  Widget build(BuildContext context) {
    final esquema = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: Esp.sm, top: Esp.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            texto.toUpperCase(),
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: esquema.primary,
              letterSpacing: 1.1,
              fontWeight: FontWeight.w700,
            ),
          ),
          if (ayuda != null) ...[
            const SizedBox(height: Esp.xs),
            Text(
              ayuda!,
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: esquema.onSurfaceVariant),
            ),
          ],
        ],
      ),
    );
  }
}

/// Una fila de formulario: etiqueta a la izquierda, valor a la derecha.
class FilaCampo extends StatelessWidget {
  const FilaCampo({
    super.key,
    required this.etiqueta,
    required this.valor,
    this.ayuda,
    this.control,
  });

  final String etiqueta;
  final String valor;
  final String? ayuda;
  final Widget? control;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: Esp.sm),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text(etiqueta, style: tema.textTheme.bodyMedium)),
              Text(
                valor,
                style: tema.textTheme.bodyMedium?.copyWith(
                  color: tema.colorScheme.primary,
                  fontWeight: FontWeight.w600,
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
            ],
          ),
          if (ayuda != null)
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                ayuda!,
                style: tema.textTheme.bodySmall?.copyWith(
                  color: tema.colorScheme.onSurfaceVariant,
                  fontSize: 11.5,
                ),
              ),
            ),
          ?control,
        ],
      ),
    );
  }
}

/// Insignia de intensidad EVA. El color sale de la rampa cálida, nunca del
/// color de marca.
class InsigniaEva extends StatelessWidget {
  const InsigniaEva(this.intensidad, {super.key, this.grande = false});

  final int intensidad;
  final bool grande;

  @override
  Widget build(BuildContext context) {
    final color = Paleta.porIntensidad(intensidad);
    return Container(
      width: grande ? 46 : 34,
      height: grande ? 46 : 34,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.18),
        shape: BoxShape.circle,
        border: Border.all(color: color, width: 1.5),
      ),
      child: Text(
        '$intensidad',
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w700,
          fontSize: grande ? 18 : 14,
          fontFeatures: const [FontFeature.tabularFigures()],
        ),
      ),
    );
  }
}

/// Estado vacío: un icono, un título y una acción opcional.
class EstadoVacio extends StatelessWidget {
  const EstadoVacio({
    super.key,
    required this.icono,
    required this.titulo,
    this.detalle,
    this.accion,
  });

  final IconData icono;
  final String titulo;
  final String? detalle;
  final Widget? accion;

  @override
  Widget build(BuildContext context) {
    final esquema = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(Esp.xl),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icono, size: 44, color: esquema.onSurfaceVariant),
            const SizedBox(height: Esp.md),
            Text(
              titulo,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            if (detalle != null) ...[
              const SizedBox(height: Esp.sm),
              Text(
                detalle!,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: esquema.onSurfaceVariant,
                ),
              ),
            ],
            if (accion != null) ...[const SizedBox(height: Esp.lg), accion!],
          ],
        ),
      ),
    );
  }
}

/// Muestra un mensaje breve en la parte inferior.
void avisar(BuildContext context, String mensaje, {bool esError = false}) {
  final esquema = Theme.of(context).colorScheme;
  ScaffoldMessenger.of(context)
    ..clearSnackBars()
    ..showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              esError ? Icons.error_outline : Icons.check_circle_outline,
              size: 18,
              color: esError ? esquema.error : Paleta.exito,
            ),
            const SizedBox(width: Esp.sm),
            Expanded(child: Text(mensaje)),
          ],
        ),
        duration: Duration(seconds: esError ? 5 : 3),
      ),
    );
}

/// Pide confirmación antes de una acción irreversible.
///
/// HU-09 lo exige: un solo toque no borra datos clínicos.
Future<bool> confirmar(
  BuildContext context, {
  required String titulo,
  required String mensaje,
  String aceptar = 'Eliminar',
  String cancelar = 'Cancelar',
}) async {
  final esquema = Theme.of(context).colorScheme;
  final resultado = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(titulo),
      content: Text(mensaje),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx, false),
          child: Text(cancelar),
        ),
        TextButton(
          onPressed: () => Navigator.pop(ctx, true),
          style: TextButton.styleFrom(foregroundColor: esquema.error),
          child: Text(aceptar),
        ),
      ],
    ),
  );
  return resultado ?? false;
}
