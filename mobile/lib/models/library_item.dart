import 'content.dart';

/// 보관함 한 줄. 내 기록과 작품이 함께 온다
class LibraryItem {
  const LibraryItem({
    required this.content,
    required this.status,
    required this.liked,
    required this.recommended,
    required this.memoPublic,
    this.rating,
    this.memo,
  });

  final Content content;
  final String status; // WISH / DOING / DONE
  final bool liked;
  final bool recommended;
  final bool memoPublic;
  final double? rating;
  final String? memo;

  factory LibraryItem.fromJson(Map<String, dynamic> json) {
    return LibraryItem(
      content: Content.fromJson(json['content'] as Map<String, dynamic>),
      status: json['status'] as String,
      liked: json['liked'] as bool? ?? false,
      recommended: json['recommended'] as bool? ?? false,
      memoPublic: json['memo_public'] as bool? ?? false,
      rating: (json['rating'] as num?)?.toDouble(),
      memo: json['memo'] as String?,
    );
  }
}
