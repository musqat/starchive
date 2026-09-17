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
    final headers = await _headers();
    final response = await _client
        .get(Uri.parse('$baseUrl$path'), headers: headers)
        .timeout(_timeout);
    return _decode(response);
  }

  Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> body,
  ) async {
    final headers = {...await _headers(), 'Content-type': 'application/json'};
    final response = await _client
        .post(
          Uri.parse('$baseUrl$path'),
          headers: headers,
          body: jsonEncode(body),
        )
        .timeout(_timeout);
    return _decode(response);
  }

  Future<Map<String, String>> _headers() async {
    final token = await readToken();
    if (token == null) return {};
    return {'Authorization': 'Bearer $token'};
  }

  Map<String, dynamic> _decode(http.Response response) {
    final text = utf8.decode(response.bodyBytes);
    final body = jsonDecode(text) as Map<String, dynamic>;
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    } else {
      final detail = body['detail'];
      throw ApiException(
        response.statusCode,
        detail is String ? detail : '요청을 처리하지 못했어요',
      );
    }
  }
}
