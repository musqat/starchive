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

  Future<void> logout() async {
    await _api.deleteToken();
    state = const AsyncData(null);
  }
}
