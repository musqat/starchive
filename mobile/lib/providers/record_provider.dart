import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_provider.dart';
import 'content_provider.dart';
import 'detail_provider.dart';
import 'library_provider.dart';
import 'memo_provider.dart';

final recordControllerProvider = Provider<RecordController>(
  RecordController.new,
);

/// 기록을 바꾸고 화면을 다시 불러온다
class RecordController {
  RecordController(this.ref);

  final Ref ref;

  /// 보낸 값만 바뀐다. 별점을 지우려면 rating 에 null 을 담아 보낸다
  Future<void> save(String contentId, Map<String, dynamic> changes) async {
    await ref.read(apiClientProvider).put('/me/records/$contentId', changes);
    _refresh(contentId);
  }

  Future<void> remove(String contentId) async {
    await ref.read(apiClientProvider).delete('/me/records/$contentId');
    _refresh(contentId);
  }

  /// 상세·목록·메모를 다시 부른다
  void _refresh(String contentId) {
    ref.invalidate(detailProvider(contentId));
    ref.invalidate(publicMemosProvider(contentId));
    ref.invalidate(popularProvider);
    ref.invalidate(recommendationsProvider);
    ref.invalidate(libraryProvider);
  }
}
