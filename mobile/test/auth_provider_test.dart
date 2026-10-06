import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:starchive/api/api_client.dart';
import 'package:starchive/providers/auth_provider.dart';

const _user = {'id': 1, 'email': 'a@b.com', 'nickname': '앱테스트'};

/// 경로별로 답하는 가짜 서버. 받은 요청을 순서대로 적어 둔다
class FakeServer {
  final calls = <String>[];
  int _issued = 0;

  /// 켜면 /auth/me 가 401 이다. 토큰이 무효인 상태
  bool tokenRevoked = false;

  Future<http.Response> handle(http.Request request) async {
    final call = '${request.method} ${request.url.path}';
    calls.add(call);

    switch (call) {
      case 'POST /auth/signup':
        return _json(_user, 201);
      case 'POST /auth/token':
        // 받을 때마다 다른 토큰을 준다. 새로 받았는지 구분하려고
        _issued++;
        return _json({'access_token': 't$_issued', 'user': _user});
      case 'GET /auth/me':
        return tokenRevoked
            ? _json({'detail': 'not authorized'}, 401)
            : _json(_user);
      case 'PATCH /auth/password':
      case 'POST /auth/withdraw':
        return http.Response('', 204);
    }
    return _json({'detail': 'not found'}, 404);
  }

  http.Response _json(Object body, [int status = 200]) =>
      http.Response.bytes(utf8.encode(jsonEncode(body)), status);
}

void main() {
  late FakeServer server;
  late ApiClient api;
  late ProviderContainer container;

  /// 저장소에 토큰을 넣어 두고 앱을 띄운다
  Future<void> start({String? token}) async {
    FlutterSecureStorage.setMockInitialValues({'access_token': ?token});
    server = FakeServer();
    api = ApiClient(client: MockClient(server.handle));
    container = ProviderContainer(
      overrides: [apiClientProvider.overrideWithValue(api)],
    );
    addTearDown(container.dispose);
  }

  AuthNotifier notifier() => container.read(authProvider.notifier);

  test('토큰이 없으면 서버를 안 부르고 로그아웃 상태', () async {
    await start();

    expect(await container.read(authProvider.future), isNull);
    expect(server.calls, isEmpty);
  });

  test('저장된 토큰이 401 이면 지우고 로그아웃 상태', () async {
    await start(token: 'dead');
    server.tokenRevoked = true;

    expect(await container.read(authProvider.future), isNull);
    expect(await api.readToken(), isNull);
  });

  test('가입하면 signup 한 번, 이어서 토큰 한 번', () async {
    await start();
    await container.read(authProvider.future);

    await notifier().signUp('a@b.com', 'password1', '앱테스트');

    expect(server.calls, ['POST /auth/signup', 'POST /auth/token']);
    expect(await api.readToken(), 't1');
    expect(container.read(authProvider).value?.nickname, '앱테스트');
  });

  test('비밀번호를 바꾸면 새 토큰을 저장한다', () async {
    await start(token: 'old');
    await container.read(authProvider.future);

    await notifier().changePassword('password1', 'password2');

    // 바꾼 순간 서버가 옛 토큰을 끊는다. 새 비밀번호로 다시 받는다
    expect(server.calls, [
      'GET /auth/me',
      'PATCH /auth/password',
      'POST /auth/token',
    ]);
    expect(await api.readToken(), 't1');
  });

  test('탈퇴하면 토큰을 지우고 로그아웃 상태', () async {
    await start(token: 'old');
    await container.read(authProvider.future);

    await notifier().withdraw('password1');

    expect(server.calls.last, 'POST /auth/withdraw');
    expect(await api.readToken(), isNull);
    expect(container.read(authProvider).value, isNull);
  });
}
