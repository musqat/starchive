import 'content.dart';

/// 검색 응답. comment 는 자연어 질의일 때만 온다
class SearchResult {
  const SearchResult({required this.items, this.comment});

  final List<Content> items;
  final String? comment;

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      items: (json['items'] as List)
          .map((e) => Content.fromJson(e as Map<String, dynamic>))
          .toList(),
      comment: json['comment'] as String?,
    );
  }
}
