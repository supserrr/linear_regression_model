import 'package:flutter_test/flutter_test.dart';

import 'package:device_price_app/main.dart';

void main() {
  testWidgets('Shows prediction form and primary CTA', (WidgetTester tester) async {
    await tester.pumpWidget(const DevicePriceApp());

    expect(find.text('Estimate price'), findsOneWidget);
    expect(
      find.text('Estimate normalized resale from your device specs.'),
      findsOneWidget,
    );
    expect(find.text('API connection'), findsOneWidget);
  });
}
