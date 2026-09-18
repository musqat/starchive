import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../providers/auth_provider.dart';

class SignUpScreen extends ConsumerStatefulWidget {
  const SignUpScreen({super.key});

  @override
  ConsumerState<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends ConsumerState<SignUpScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _nickname = TextEditingController();
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _nickname.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _submitting = true;
      _error = null;
    });

    String? error;
    try {
      await ref
          .read(authProvider.notifier)
          .signUp(_email.text, _password.text, _nickname.text);
    } on ApiException catch (e) {
      error = switch (e.statusCode) {
        409 => '이미 쓰는 이메일이에요',
        422 => '입력한 값을 다시 확인해 주세요',
        _ => e.message,
      };
    } catch (_) {
      error = '서버에 연결하지 못했어요';
    }

    if (!mounted) return;
    // 가입과 로그인이 함께 끝난다. 로그인 화면까지 걷어내고 홈으로
    if (error == null) {
      Navigator.of(context).pop();
      return;
    }
    setState(() {
      _submitting = false;
      _error = error;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('가입')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _email,
              decoration: const InputDecoration(labelText: '이메일'),
              keyboardType: TextInputType.emailAddress,
              autocorrect: false,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _password,
              decoration: const InputDecoration(
                labelText: '비밀번호',
                helperText: '8자 이상',
              ),
              obscureText: true,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _nickname,
              decoration: const InputDecoration(labelText: '닉네임'),
            ),
            const SizedBox(height: 16),
            if (_error != null)
              Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _submitting ? null : _submit,
              child: Text(_submitting ? '가입 중' : '가입'),
            ),
          ],
        ),
      ),
    );
  }
}
