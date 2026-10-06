import 'package:flutter_test/flutter_test.dart';

import 'package:starchive/models/content.dart';
import 'package:starchive/models/library_item.dart';
import 'package:starchive/models/recommendation.dart';

/// 목록 응답의 작품 한 편. 테스트마다 필요한 키만 덮어쓴다
Map<String, dynamic> contentJson([Map<String, dynamic> extra = const {}]) => {
  'id': 'tmdb_680',
  'type': 'MOVIE',
  'title': '펄프 픽션',
  'creator': '쿠엔틴 타란티노',
  'image_url': null,
  'external_rating': 8.5,
  ...extra,
};

/// 추천 응답. 테스트마다 필요한 키만 덮어쓴다
Map<String, dynamic> recommendationJson([
  Map<String, dynamic> extra = const {},
]) => {
  'items': [],
  'generated_at': null,
  'rated_count': 2,
  'required_count': 5,
  'required_rating': 3.0,
  ...extra,
};

void main() {
  group('Content', () {
    test('로그인했으면 내 별점을 읽는다', () {
      final content = Content.fromJson(contentJson({'my_rating': 4}));

      // 정수로 와도 double 로 읽는다
      expect(content.myRating, 4.0);
    });

    test('로그인 전 응답에는 내 별점이 없다', () {
      final content = Content.fromJson(contentJson());

      expect(content.myRating, isNull);
    });

    test('외부 평점이 없는 작품도 읽는다', () {
      final content = Content.fromJson(contentJson({'external_rating': null}));

      expect(content.externalRating, isNull);
    });
  });

  group('LibraryItem', () {
    test('작품은 목록이 아니라 한 편이다', () {
      final item = LibraryItem.fromJson({
        'content': contentJson(),
        'status': 'DONE',
        'rating': 4.0,
        'liked': true,
        'recommended': false,
        'memo': '좋다',
        'memo_public': true,
      });

      expect(item.content.title, '펄프 픽션');
      expect(item.rating, 4.0);
      expect(item.memoPublic, isTrue);
    });

    test('좋아요·추천·공개가 빠지면 false 로 읽는다', () {
      final item = LibraryItem.fromJson({
        'content': contentJson(),
        'status': 'WISH',
      });

      expect(item.liked, isFalse);
      expect(item.recommended, isFalse);
      expect(item.memoPublic, isFalse);
    });
  });

  group('RecommendationList', () {
    test('한 번도 안 만들었으면 만든 시각이 null', () {
      final list = RecommendationList.fromJson(recommendationJson());

      expect(list.generatedAt, isNull);
      expect(list.remaining, 3);
    });

    test('만든 시각을 DateTime 으로 읽는다', () {
      final list = RecommendationList.fromJson(
        recommendationJson({'generated_at': '2026-09-18T01:20:00'}),
      );

      expect(list.generatedAt!.month, 9);
      expect(list.generatedAt!.day, 18);
    });
  });
}
