import 'package:flutter_test/flutter_test.dart';

import 'package:starchive/main.dart';

void main() {
  // 네트워크는 부르지 않는다. 버튼을 누르기 전 첫 화면만 본다
  testWidgets('첫 화면에 서버 주소와 확인 버튼이 보인다', (tester) async {
    await tester.pumpWidget(const StarchiveApp());

    expect(find.text(apiBaseUrl), findsOneWidget);
    expect(find.text('확인'), findsOneWidget);
  });
}
