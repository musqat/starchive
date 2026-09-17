import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'models/user.dart';
import 'providers/auth_provider.dart';
import 'screens/login_screen.dart';

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
      theme: ThemeData(colorSchemeSeed: Colors.indigo),
      home: auth.when(
        loading: () =>
            const Scaffold(body: Center(child: CircularProgressIndicator())),
        // 시작 확인이 실패해도 로그인은 할 수 있게 한다
        error: (_, _) => const LoginScreen(),
        data: (user) =>
            user == null ? const LoginScreen() : SignedInScreen(user: user),
      ),
    );
  }
}

/// 3단계에서 홈 화면으로 바뀐다
class SignedInScreen extends ConsumerWidget {
  const SignedInScreen({super.key, required this.user});

  final User user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('starchive')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('${user.nickname} 님'),
            const SizedBox(height: 16),
            OutlinedButton(
              onPressed: () => ref.read(authProvider.notifier).logout(),
              child: const Text('로그아웃'),
            ),
          ],
        ),
      ),
    );
  }
}
