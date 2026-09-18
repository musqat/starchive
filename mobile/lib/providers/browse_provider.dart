import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/content.dart';
import '../models/content_page.dart';
import 'auth_provider.dart';

/// 한 번에 받는 개수
const pageSize = 20;

/// 목록 화면의 필터. 바뀌면 1쪽부터 다시 받는다
class BrowseFilter {
  const BrowseFilter({
    required this.type,
    this.genre,
    this.sort = 'popular',
    this.order = 'desc',
    this.unseen = false,
  });

  final String type; // MOVIE / BOOK
  final String? genre;
  final String sort; // popular / rating / recent
  final String order; // desc / asc
  final bool unseen;

  BrowseFilter copyWith({
    String? genre,
    String? sort,
    String? order,
    bool? unseen,
    bool clearGenre = false,
  }) {
    return BrowseFilter(
      type: type,
      genre: clearGenre ? null : (genre ?? this.genre),
      sort: sort ?? this.sort,
      order: order ?? this.order,
      unseen: unseen ?? this.unseen,
    );
  }

  /// provider 를 구분하는 키. 필드가 하나라도 다르면 다른 값이어야 한다
  @override
  bool operator ==(Object other) =>
      other is BrowseFilter &&
      other.type == type &&
      other.genre == genre &&
      other.sort == sort &&
      other.order == order &&
      other.unseen == unseen;

  @override
  int get hashCode => Object.hash(type, genre, sort, order, unseen);

  String toQuery({required int page}) {
    final parts = [
      'type=$type',
      'sort=$sort',
      'order=$order',
      'page=$page',
      'size=$pageSize',
      // 장르는 한글이라 그대로 붙이면 깨진다
      if (genre != null) 'genre=${Uri.encodeQueryComponent(genre!)}',
      // 끈 상태를 보내면 서버가 false 로 받는다. 켰을 때만 넣는다
      if (unseen) 'unseen=true',
    ];
    return '?${parts.join('&')}';
  }
}

/// 그 매체에 있는 장르 목록
final genresProvider = FutureProvider.family<List<String>, String>((
  ref,
  type,
) async {
  final api = ref.read(apiClientProvider);
  final list = await api.getList('/contents/genres?type=$type');
  return list.cast<String>();
});

/// 필터별 목록. 아래로 내리면 다음 쪽을 이어 붙인다
final browseProvider =
    AsyncNotifierProvider.family<BrowseNotifier, List<Content>, BrowseFilter>(
      BrowseNotifier.new,
    );

/// Riverpod 3 은 family 전용 Notifier 가 없다. 인자를 생성자로 받는다
class BrowseNotifier extends AsyncNotifier<List<Content>> {
  BrowseNotifier(this.filter);

  final BrowseFilter filter;

  int _page = 1;
  bool _hasMore = true;
  bool _loadingMore = false;

  bool get hasMore => _hasMore;

  Future<ContentPage> _fetch(int page) async {
    final api = ref.read(apiClientProvider);
    final body = await api.get('/contents${filter.toQuery(page: page)}');
    return ContentPage.fromJson(body);
  }

  @override
  Future<List<Content>> build() async {
    // 로그인 상태가 바뀌면 unseen 결과가 달라진다
    ref.watch(authProvider);

    final first = await _fetch(1);
    _page = 1;
    _hasMore = first.hasMore;
    return first.items;
  }

  /// 목록 끝에 닿았을 때 부른다
  Future<void> loadMore() async {
    if (_loadingMore || !_hasMore) return;
    _loadingMore = true;

    try {
      final next = await _fetch(_page + 1);
      _page += 1;
      _hasMore = next.hasMore;
      state = AsyncData([...?state.value, ...next.items]);
    } catch (_) {
      // 다음 쪽을 못 받아도 이미 받은 목록은 그대로 둔다
      _hasMore = false;
    } finally {
      _loadingMore = false;
    }
  }
}
