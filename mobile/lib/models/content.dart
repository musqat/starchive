class Content {
  const Content({
    required this.id,
    required this.type,
    required this.title,
    this.creator,
    this.imageUrl,
    this.externalRating,
  });

  final String id;
  final String type; // MOVIE / BOOK
  final String title;
  final String? creator;
  final String? imageUrl;

  /// TMDB·알라딘 평점. 없는 작품도 있다
  final double? externalRating;

  factory Content.fromJson(Map<String, dynamic> json) {
    return Content(
      id: json['id'] as String,
      type: json['type'] as String,
      title: json['title'] as String,
      creator: json['creator'] as String?,
      imageUrl: json['image_url'] as String?,
      externalRating: (json['external_rating'] as num?)?.toDouble(),
    );
  }
}
