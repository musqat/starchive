import 'content.dart';

/// 보관함 한 줄. 내 기록과 작품이 함께 온다
class LibraryItem {
  const LibraryItem({
    required this.content,
    required this.status,
    required this.liked,
    required this.recommended,
    this.rating,
    this.memo,
  });

  final Content content;
  final String status; // WISH / DOING / DONE
  final bool liked;
  final bool recommended;
  final double? rating;
  final String? memo;

  factory LibraryItem.fromJson(Map<String, dynamic> json) {
    // TODO: content 는 중첩 맵이다
    //       rating 은 num? 뒤 toDouble(), liked·recommended 는 bool
    throw UnimplementedError();
  }
}
