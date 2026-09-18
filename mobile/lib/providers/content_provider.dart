import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/content.dart';
import '../models/recommendation.dart';
import 'auth_provider.dart';

/// 인기 목록. type 은 'MOVIE' 나 'BOOK'
final popularProvider = FutureProvider.family<List<Content>, String>((
  ref,
  type,
) async {
  // 로그인하면 내 별점이 함께 온다.
  ref.watch(authProvider);
  final api = ref.read(apiClientProvider);
  final body = await api.get('/contents?type=$type&size=10');
  return (body['items'] as List)
      .map((e) => Content.fromJson(e as Map<String, dynamic>))
      .toList();
});

/// 매체별 추천
final recommendationsProvider =
    FutureProvider.family<RecommendationList, String>((ref, type) async {
      ref.watch(authProvider);
      final api = ref.read(apiClientProvider);
      return RecommendationList.fromJson(
        await api.get('/recommendations?type=$type'),
      );
    });
