class Content {
  const Content({
    required this.id,
    required this.type,
    required this.title,
    this.creator,
    this.imageUrl,
  });

  final String id;
  final String type; // MOVIE / BOOK
  final String title;
  final String? creator;
  final String? imageUrl;

  factory Content.fromJson(Map<String, dynamic> json) {
    return Content(
      id: json['id'] as String,
      type: json['type'] as String,
      title: json['title'] as String,
      creator: json['creator'] as String?,
      imageUrl: json['image_url'] as String?,
    );
  }
}
