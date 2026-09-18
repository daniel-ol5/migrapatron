import 'package:flutter/material.dart';

import 'core/config.dart';

void main() {
  runApp(const MigraPatronApp());
}

class MigraPatronApp extends StatelessWidget {
  const MigraPatronApp({super.key});

  static const _semilla = Color(0xFF4B3F8C);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MigraPatrón IA',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: _semilla),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: _semilla,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const PantallaAndamiaje(),
    );
  }
}

/// Pantalla temporal que confirma que el proyecto compila y corre.
/// Se reemplaza por el splash router en HU-03.
class PantallaAndamiaje extends StatelessWidget {
  const PantallaAndamiaje({super.key});

  static const _pendientes = <(String, String, String)>[
    ('Iniciar sesión', 'HU-03', 'CU-02'),
    ('Bitácora del día', 'HU-05', 'CU-05'),
    ('Registrar episodio', 'HU-06', 'CU-06'),
    ('Historial', 'HU-07', 'CU-07'),
    ('Mis patrones', 'HU-15', 'CU-10'),
    ('Resumen clínico', 'HU-18', 'CU-13'),
  ];

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('MigraPatrón IA'),
        backgroundColor: tema.colorScheme.surfaceContainerHighest,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text('El andamiaje está en pie', style: tema.textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(
            'El proyecto compila. Las pantallas se construyen en el Sprint 1.',
            style: tema.textTheme.bodyMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Backend: ${Config.apiUrl}',
            style: tema.textTheme.bodySmall?.copyWith(
              fontFamily: 'monospace',
              color: tema.colorScheme.primary,
            ),
          ),
          const SizedBox(height: 24),
          Card(
            margin: EdgeInsets.zero,
            child: Column(
              children: [
                for (final (titulo, historia, caso) in _pendientes)
                  ListTile(
                    dense: true,
                    title: Text(titulo),
                    trailing: Text(
                      '$historia · $caso',
                      style: tema.textTheme.labelSmall?.copyWith(
                        fontFamily: 'monospace',
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: tema.colorScheme.tertiaryContainer,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              Config.avisoNoCausalidad,
              style: tema.textTheme.bodySmall?.copyWith(
                color: tema.colorScheme.onTertiaryContainer,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
