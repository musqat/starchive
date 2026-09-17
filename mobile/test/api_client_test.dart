import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:starchive/api/api_client.dart';

void main() {
  // 테스트에는 기기 저장소가 없다. 메모리 저장소로 바꾼다
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('토큰이 있으면 Bearer 헤더를 붙인다', () async {
    String? sentAuth;
    final api = ApiClient(
      client: MockClient((request) async {
        sentAuth = request.headers['authorization'];
        return http.Response('{}', 200);
      }),
    );

    await api.saveToken('abc');
    await api.get('/auth/me');

    expect(sentAuth, 'Bearer abc');
  });

  test('토큰이 없으면 헤더를 안 붙인다', () async {
    String? sentAuth;
    final api = ApiClient(
      client: MockClient((request) async {
        sentAuth = request.headers['authorization'];
        return http.Response('{}', 200);
      }),
    );

    await api.get('/contents');

    expect(sentAuth, isNull);
  });

  test('401 이면 상태 코드를 담은 ApiException', () async {
    final api = ApiClient(
      client: MockClient(
        (_) async => http.Response('{"detail":"not authorized"}', 401),
      ),
    );

    expect(
      () => api.get('/auth/me'),
      throwsA(
        isA<ApiException>()
            .having((e) => e.statusCode, 'statusCode', 401)
            .having((e) => e.message, 'message', 'not authorized'),
      ),
    );
  });

  test('한글 detail 이 깨지지 않는다', () async {
    // 백엔드 응답처럼 charset 을 붙이지 않는다. 그래도 utf8 로 읽어야 한다
    final api = ApiClient(
      client: MockClient(
        (_) async => http.Response.bytes(
          utf8.encode('{"detail":"3분 뒤에 다시 시도해주세요"}'),
          429,
        ),
      ),
    );

    await expectLater(
      () => api.post('/auth/token', {'email': 'a@b.com', 'password': 'x'}),
      throwsA(
        isA<ApiException>().having(
          (e) => e.message,
          'message',
          '3분 뒤에 다시 시도해주세요',
        ),
      ),
    );
  });

  test('detail 이 문자열이 아니면 기본 문구', () async {
    final api = ApiClient(
      client: MockClient(
        (_) async => http.Response('{"detail":[{"loc":["body"]}]}', 422),
      ),
    );

    expect(
      () => api.post('/auth/token', {}),
      throwsA(
        isA<ApiException>().having(
          (e) => e.message,
          'message',
          '요청을 처리하지 못했어요',
        ),
      ),
    );
  });
}
