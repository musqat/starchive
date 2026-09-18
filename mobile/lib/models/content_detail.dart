/// 상세 응답. 목록보다 줄거리·개봉일·메타가 더 온다
class ContentDetail {
  const ContentDetail({
    required this.id,
    required this.type,
    required this.title,
    required this.genre,
    required this.metadata,
    this.creator,
    this.imageUrl,
    this.description,
    this.releaseDate,
    this.externalRating,
    this.externalPopularity,
    this.myMemo,
    this.myMemoPublic = false,
  });

  final String id;
  final String type;
  final String title;
  final List<String> genre;

  /// 매체마다 다르다. 영화는 runtime·providers, 책은 itemId
  final Map<String, dynamic> metadata;

  final String? creator;
  final String? imageUrl;
  final String? description;
  final String? releaseDate;
  final double? externalRating;
  final int? externalPopularity;

  /// 로그인했을 때만 채워진다
  final String? myMemo;
  final bool myMemoPublic;

  /// 영화 러닝타임(분). 책이면 null
  int? get runtime => metadata['runtime'] as int?;

  factory ContentDetail.fromJson(Map<String, dynamic> json) {
    return ContentDetail(
      id: json['id'] as String,
      type: json['type'] as String,
      title: json['title'] as String,
      genre: (json['genre'] as List?)?.cast<String>() ?? [],
      metadata: json['content_metadata'] as Map<String, dynamic>? ?? {},
      creator: json['creator'] as String?,
      imageUrl: json['image_url'] as String?,
      description: json['description'] as String?,
      releaseDate: json['release_date'] as String?,
      externalRating: (json['external_rating'] as num?)?.toDouble(),
      externalPopularity: json['external_popularity'] as int?,
      myMemo: json['my_memo'] as String?,
      myMemoPublic: json['my_memo_public'] as bool? ?? false,
    );
  }
}
