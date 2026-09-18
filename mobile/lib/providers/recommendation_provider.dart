import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_provider.dart';
import 'content_provider.dart';

final recommendationControllerProvider = Provider<RecommendationController>(
  RecommendationController.new,
);

/// 추천 다시 만들기. 매체 둘이 함께 바뀐다
class RecommendationController {
  RecommendationController(this.ref);

  final Ref ref;

  /// LLM 을 부르므로 서버가 60분 쿨다운을 둔다
  Future<void> refresh() async {
    final api = ref.read(apiClientProvider);
    await api.post('/me/recommendations/refresh', {});
    ref.invalidate(recommendationsProvider);
  }
}
