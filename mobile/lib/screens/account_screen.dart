import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/user.dart';
import '../providers/auth_provider.dart';

class AccountScreen extends ConsumerWidget {
  const AccountScreen({super.key, required this.user});

  final User user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('계정')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Text(user.nickname, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text(user.email, style: Theme.of(context).textTheme.bodySmall),
          const Divider(height: 40),
          const _PasswordForm(),
          const Divider(height: 40),
          const _WithdrawForm(),
        ],
      ),
    );
  }
}

class _PasswordForm extends ConsumerStatefulWidget {
  const _PasswordForm();

  @override
  ConsumerState<_PasswordForm> createState() => _PasswordFormState();
}

class _PasswordFormState extends ConsumerState<_PasswordForm> {
  final _current = TextEditingController();
  final _next = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _submitting = true);

    String? error;
    try {
      await ref
          .read(authProvider.notifier)
          .changePassword(_current.text, _next.text);
    } on ApiException catch (e) {
      error = switch (e.statusCode) {
        403 => '현재 비밀번호가 틀려요',
        422 => '새 비밀번호는 8자 이상이에요',
        _ => e.message,
      };
    } catch (_) {
      error = '서버에 연결하지 못했어요';
    }

    if (!mounted) return;
    setState(() {
      _submitting = false;
      if (error == null) {
        _current.clear();
        _next.clear();
      }
    });
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? '비밀번호를 바꿨어요')));
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('비밀번호 변경', style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 12),
        TextField(
          controller: _current,
          decoration: const InputDecoration(labelText: '현재 비밀번호'),
          obscureText: true,
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _next,
          decoration: const InputDecoration(
            labelText: '새 비밀번호',
            helperText: '8자 이상. 다른 기기의 로그인은 모두 끊긴다',
          ),
          obscureText: true,
        ),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: Text(_submitting ? '바꾸는 중' : '변경'),
        ),
      ],
    );
  }
}

class _WithdrawForm extends ConsumerStatefulWidget {
  const _WithdrawForm();

  @override
  ConsumerState<_WithdrawForm> createState() => _WithdrawFormState();
}

class _WithdrawFormState extends ConsumerState<_WithdrawForm> {
  final _password = TextEditingController();
  bool _confirming = false;
  bool _submitting = false;

  @override
  void dispose() {
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _submitting = true);

    String? error;
    try {
      await ref.read(authProvider.notifier).withdraw(_password.text);
    } on ApiException catch (e) {
      error = e.message;
    } catch (_) {
      error = '서버에 연결하지 못했어요';
    }

    if (!mounted) return;
    // 탈퇴하면 로그아웃 상태다. 홈으로 돌려보낸다
    if (error == null) {
      Navigator.of(context).pop();
      return;
    }
    setState(() => _submitting = false);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error)));
  }

  @override
  Widget build(BuildContext context) {
    final danger = Theme.of(context).colorScheme.error;

    if (!_confirming) {
      return TextButton(
        onPressed: () => setState(() => _confirming = true),
        style: TextButton.styleFrom(foregroundColor: danger),
        child: const Text('탈퇴'),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('탈퇴', style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 4),
        const Text('남긴 기록과 메모도 함께 지워진다. 되돌릴 수 없다'),
        const SizedBox(height: 12),
        TextField(
          controller: _password,
          decoration: const InputDecoration(labelText: '비밀번호'),
          obscureText: true,
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            TextButton(
              onPressed: _submitting
                  ? null
                  : () => setState(() => _confirming = false),
              child: const Text('취소'),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _submitting ? null : _submit,
              style: FilledButton.styleFrom(backgroundColor: danger),
              child: Text(_submitting ? '처리 중' : '탈퇴'),
            ),
          ],
        ),
      ],
    );
  }
}
