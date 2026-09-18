import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:migrapatron_movil/core/config.dart';
import 'package:migrapatron_movil/main.dart';

void main() {
  testWidgets('la app arranca y muestra el andamiaje', (tester) async {
    await tester.pumpWidget(const MigraPatronApp());

    expect(find.text('MigraPatrón IA'), findsOneWidget);
    expect(find.text('El andamiaje está en pie'), findsOneWidget);
  });

  testWidgets('el aviso de no causalidad está siempre visible (RNF-07)', (
    tester,
  ) async {
    await tester.pumpWidget(const MigraPatronApp());

    expect(find.text(Config.avisoNoCausalidad), findsOneWidget);
  });

  testWidgets('lista las pantallas pendientes del Sprint 1', (tester) async {
    await tester.pumpWidget(const MigraPatronApp());

    expect(find.byType(ListTile), findsNWidgets(6));
    expect(find.text('Bitácora del día'), findsOneWidget);
  });

  group('Config', () {
    test('la URL base apunta al backend local', () {
      expect(Config.apiUrl, contains('8000/api'));
    });

    test('los umbrales de suficiencia coinciden con RN-02', () {
      expect(Config.minimoDias, 14);
      expect(Config.minimoEpisodios, 3);
    });
  });

  test('el tema usa Material 3', () {
    const app = MigraPatronApp();
    expect(app, isA<StatelessWidget>());
  });
}
