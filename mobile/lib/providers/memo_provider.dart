import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/public_memo.dart';
import 'auth_provider.dart';

/// 해당 작품의 공개 메모 목록
final publicMemosProvider = FutureProvider.family<List<PublicMemo>, String>((
  ref,
  id,
) async {
  // 백엔드가 내 메모를 목록에서 뺀다. 로그인 상태가 바뀌면 다시 부른다
  ref.watch(authProvider);
  final api = ref.read(apiClientProvider);
  final list = await api.getList('/contents/$id/memos');
  return list
      .map((e) => PublicMemo.fromJson(e as Map<String, dynamic>))
      .toList();
});
