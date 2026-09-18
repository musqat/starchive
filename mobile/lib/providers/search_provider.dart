import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/search_result.dart';
import 'auth_provider.dart';

/// 검색. 검색어가 비면 부르지 않는다
final searchProvider = FutureProvider.family<SearchResult?, String>((
  ref,
  query,
) async {
  if (query.isEmpty) {
    return null;
  }
  final api = ref.read(apiClientProvider);

  return SearchResult.fromJson(
    await api.get('/search?q=${Uri.encodeQueryComponent(query)}'),
  );
});
