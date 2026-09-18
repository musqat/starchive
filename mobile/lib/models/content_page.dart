import 'content.dart';

/// 목록 응답. total 은 이 쪽이 아니라 필터 전체 개수
class ContentPage {
  const ContentPage({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
  });

  final List<Content> items;
  final int total;
  final int page;
  final int size;

  /// 이번 쪽까지 받은 개수가 전체보다 적으면 더 있다
  bool get hasMore => page * size < total;

  factory ContentPage.fromJson(Map<String, dynamic> json) {
    return ContentPage(
      items: (json['items'] as List)
          .map((e) => Content.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      size: json['size'] as int,
    );
  }
}
