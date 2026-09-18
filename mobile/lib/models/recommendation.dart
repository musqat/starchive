import 'content.dart';

/// 추천 한 편. reason 은 재랭킹이 쓴 한 줄
class Recommendation {
  const Recommendation({required this.content, this.reason});

  final Content content;
  final String? reason;

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      content: Content.fromJson(json['content'] as Map<String, dynamic>),
      reason: json['reason'] as String?,
    );
  }
}

/// 매체별 추천. items 가 비면 기록이 모자란 것
class RecommendationList {
  const RecommendationList({
    required this.items,
    required this.ratedCount,
    required this.requiredCount,
    required this.requiredRating,
    this.generatedAt,
  });

  final List<Recommendation> items;

  /// 마지막으로 만든 시각. 한 번도 안 만들었으면 null
  final DateTime? generatedAt;
  final int ratedCount;
  final int requiredCount;
  final double requiredRating;

  /// 추천을 열려면 몇 편이 더 필요한가
  int get remaining => requiredCount - ratedCount;

  factory RecommendationList.fromJson(Map<String, dynamic> json) {
    return RecommendationList(
      items: (json['items'] as List)
          .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
          .toList(),
      generatedAt: json['generated_at'] == null
          ? null
          : DateTime.parse(json['generated_at'] as String),
      ratedCount: json['rated_count'] as int,
      requiredCount: json['required_count'] as int,
      requiredRating: (json['required_rating'] as num).toDouble(),

      // TODO: generated_at 은 문자열이거나 null 이다. DateTime.parse 로 바꾼다
    );
  }
}
