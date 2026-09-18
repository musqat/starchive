import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/user.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

/// 로그인한 사용자. null 이면 로그아웃 상태
final authProvider = AsyncNotifierProvider<AuthNotifier, User?>(
  AuthNotifier.new,
);

class AuthNotifier extends AsyncNotifier<User?> {
  ApiClient get _api => ref.read(apiClientProvider);

  /// 앱 시작 때 한 번 돈다
  @override
  Future<User?> build() async {
    if (await _api.readToken() == null) {
      return null;
    }
    try {
      final body = await _api.get('/auth/me');
      return User.fromJson(body);
    } on ApiException catch (e) {
      if (e.statusCode != 401) rethrow;
      await _api.deleteToken();
      return null;
    }
  }

  Future<void> login(String email, String password) async {
    final body = await _api.post('/auth/token', {
      'email': email,
      'password': password,
    });
    await _api.saveToken(body['access_token'] as String);
    state = AsyncData(User.fromJson(body['user'] as Map<String, dynamic>));
  }

  /// 가입만으로는 로그인이 안 된다. 이어서 토큰을 받는다
  Future<void> signUp(String email, String password, String nickname) async {
    await _api.post('/auth/signup', {
      'email': email,
      'password': password,
      'nickname': nickname,
    });

    await login(email, password);
  }

  /// 바꾸면 서버가 token_version 을 올려 지금 토큰이 죽는다
  Future<void> changePassword(String current, String next) async {
    final email = state.value?.email;
    if (email == null) return;

    await _api.patch('/auth/password', {
      'current_password': current,
      'new_password': next,
    });
    await login(email, next);
  }

  /// 기록도 함께 지워진다
  Future<void> withdraw(String password) async {
    await _api.postNoContent('/auth/withdraw', {'password': password});
    await _api.deleteToken();
    state = const AsyncData(null);
  }

  Future<void> logout() async {
    await _api.deleteToken();
    state = const AsyncData(null);
  }
}
