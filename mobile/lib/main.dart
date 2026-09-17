import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers/auth_provider.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const ProviderScope(child: StarchiveApp()));
}

class StarchiveApp extends ConsumerWidget {
  const StarchiveApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);

    return MaterialApp(
      title: 'starchive',
      // 웹과 같은 어두운 바탕(#0c0c0c). 밝은 테마는 두지 않는다
      theme: ThemeData(
        brightness: Brightness.dark,
        colorSchemeSeed: Colors.indigo,
        scaffoldBackgroundColor: const Color(0xFF0C0C0C),
        appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF0C0C0C)),
      ),
      home: auth.when(
        loading: () =>
            const Scaffold(body: Center(child: CircularProgressIndicator())),
        // 시작 확인이 실패해도 목록은 볼 수 있다
        error: (_, _) => const HomeScreen(user: null),
        data: (user) => HomeScreen(user: user),
      ),
    );
  }
}
