import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:starchive/screens/login_screen.dart';

void main() {
  testWidgets('로그인 화면에 입력칸 둘과 버튼이 보인다', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: LoginScreen())),
    );

    expect(find.widgetWithText(TextField, '이메일'), findsOneWidget);
    expect(find.widgetWithText(TextField, '비밀번호'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, '로그인'), findsOneWidget);
  });
}
