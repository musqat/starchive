import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

// 에뮬레이터에서 10.0.2.2 는 PC 의 localhost
const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

/// 2xx 가 아닌 응답
class ApiException implements Exception {
  const ApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => 'ApiException($statusCode, $message)';
}

class ApiClient {
  ApiClient({
    http.Client? client,
    FlutterSecureStorage? storage,
    this.baseUrl = apiBaseUrl,
  }) : _client = client ?? http.Client(),
       _storage = storage ?? const FlutterSecureStorage();

  static const _tokenKey = 'access_token';
  static const _timeout = Duration(seconds: 10);

  final http.Client _client;
  final FlutterSecureStorage _storage;
  final String baseUrl;

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<void> saveToken(String token) =>
      _storage.write(key: _tokenKey, value: token);

  Future<void> deleteToken() => _storage.delete(key: _tokenKey);

  Future<Map<String, dynamic>> get(String path) async {
    final response = await _client
        .get(Uri.parse('$baseUrl$path'), headers: await _headers())
        .timeout(_timeout);
    return _parse(response) as Map<String, dynamic>;
  }

  /// 응답이 목록인 API. /contents/{id}/memos 같은 것
  Future<List<dynamic>> getList(String path) async {
    final response = await _client
        .get(Uri.parse('$baseUrl$path'), headers: await _headers())
        .timeout(_timeout);
    return _parse(response) as List<dynamic>;
  }

  Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await _client
        .post(
          Uri.parse('$baseUrl$path'),
          headers: await _jsonHeaders(),
          body: jsonEncode(body),
        )
        .timeout(_timeout);
    return _parse(response) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> put(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await _client
        .put(
          Uri.parse('$baseUrl$path'),
          headers: await _jsonHeaders(),
          body: jsonEncode(body),
        )
        .timeout(_timeout);
    return _parse(response) as Map<String, dynamic>;
  }

  /// 성공은 204 라 돌려줄 본문이 없다
  Future<void> delete(String path) async {
    final response = await _client
        .delete(Uri.parse('$baseUrl$path'), headers: await _headers())
        .timeout(_timeout);
    if (response.statusCode >= 300) {
      _parse(response); // 예외를 던진다
    }
  }

  Future<Map<String, String>> _headers() async {
    final token = await readToken();
    if (token == null) return {};
    return {'Authorization': 'Bearer $token'};
  }

  Future<Map<String, String>> _jsonHeaders() async => {
    ...await _headers(),
    'Content-Type': 'application/json',
  };

  /// 본문을 읽고 2xx 가 아니면 예외. 맵이거나 목록이다
  dynamic _parse(http.Response response) {
    // response.body 로 읽으면 한글이 깨진다. 백엔드 JSON 에 charset 표시가 없다
    final text = utf8.decode(response.bodyBytes);
    final body = jsonDecode(text);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }

    // 422 는 detail 이 목록이라 문자열일 때만 쓴다
    final detail = body is Map ? body['detail'] : null;
    throw ApiException(
      response.statusCode,
      detail is String ? detail : '요청을 처리하지 못했어요',
    );
  }
}
