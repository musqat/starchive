/// 공개로 켠 남의 메모
class PublicMemo {
  const PublicMemo({
    required this.nickname,
    required this.memo,
    required this.updatedAt,
    this.rating,
  });

  final String nickname;
  final String memo;
  final DateTime updatedAt;
  final double? rating;

  factory PublicMemo.fromJson(Map<String, dynamic> json) {
    return PublicMemo(
      nickname: json['nickname'] as String,
      memo: json['memo'] as String,
      updatedAt: DateTime.parse(json['updated_at'] as String),
      rating: (json['rating'] as num?)?.toDouble(),
    );
  }
}
