import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/content_detail.dart';
import 'auth_provider.dart';

/// 작품 하나. id 는 'tmdb_157336' 같은 값
final detailProvider = FutureProvider.family<ContentDetail, String>((
  ref,
  id,
) async {
  ref.watch(authProvider);
  final api = ref.read(apiClientProvider);
  return ContentDetail.fromJson(await api.get('/contents/$id'));
});
