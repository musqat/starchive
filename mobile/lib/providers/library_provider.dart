import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/library_item.dart';
import 'auth_provider.dart';

/// 보관함 탭. 웹과 같은 넷
enum LibraryTab {
  all('전체'),
  liked('좋아요'),
  recommended('추천해요'),
  memo('댓글');

  const LibraryTab(this.label);

  final String label;

  /// 탭마다 파라미터가 하나씩 붙는다
  String get query => switch (this) {
    LibraryTab.all => '',
    LibraryTab.liked => '&liked=true',
    LibraryTab.recommended => '&recommended=true',
    LibraryTab.memo => '&has_memo=true',
  };
}

/// 탭별 보관함. 로그인해야 부를 수 있다
final libraryProvider = FutureProvider.family<List<LibraryItem>, LibraryTab>((
  ref,
  tab,
) async {
  ref.watch(authProvider);
  final api = ref.read(apiClientProvider);
  final list = await api.getList('/me/library?page=1&size=50${tab.query}');
  return list
      .map((e) => LibraryItem.fromJson(e as Map<String, dynamic>))
      .toList();
});
