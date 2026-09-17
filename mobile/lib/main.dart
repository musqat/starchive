import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

// 백엔드 주소
// 기본값 10.0.2.2 는 Android 에뮬레이터에서 본 PC 의 localhost
const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

void main() {
  runApp(const StarchiveApp());
}

class StarchiveApp extends StatelessWidget {
  const StarchiveApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'starchive',
      theme: ThemeData(colorSchemeSeed: Colors.indigo),
      home: const HealthScreen(),
    );
  }
}

/// GET /health 결과를 보여 준다
class HealthScreen extends StatefulWidget {
  const HealthScreen({super.key});

  @override
  State<HealthScreen> createState() => _HealthScreenState();
}

class _HealthScreenState extends State<HealthScreen> {
  String _result = '아직 확인하지 않았다';
  bool _loading = false;

  Future<void> _checkHealth() async {
    setState(() => _loading = true);

    String result;
    try {
      final response = await http
          .get(Uri.parse('$apiBaseUrl/health'))
          .timeout(const Duration(seconds: 10));
      result = '${response.statusCode} ${response.body}';
    } catch (e) {
      result = '연결 실패: $e';
    }

    if (!mounted) return;
    setState(() {
      _result = result;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('서버 연결 확인')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(apiBaseUrl, style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(height: 16),
              Text(_result, textAlign: TextAlign.center),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _loading ? null : _checkHealth,
                child: Text(_loading ? '확인 중' : '확인'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
