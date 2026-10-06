import 'package:flutter_test/flutter_test.dart';

import 'package:starchive/providers/browse_provider.dart';

void main() {
  group('필터 비교', () {
    // provider 가 필터를 키로 쓴다. 같은 값이면 같은 목록을 돌려준다
    test('필드가 같으면 같은 필터다', () {
      const a = BrowseFilter(type: 'MOVIE', genre: '드라마');
      const b = BrowseFilter(type: 'MOVIE', genre: '드라마');

      expect(a, b);
      expect(a.hashCode, b.hashCode);
    });

    test('하나라도 다르면 다른 필터다', () {
      const base = BrowseFilter(type: 'MOVIE');

      expect(base == base.copyWith(sort: 'rating'), isFalse);
      expect(base == base.copyWith(order: 'asc'), isFalse);
      expect(base == base.copyWith(unseen: true), isFalse);
      expect(base == base.copyWith(genre: '드라마'), isFalse);
    });
  });

  group('copyWith', () {
    test('장르를 null 로 넘겨도 지워지지 않는다', () {
      const filter = BrowseFilter(type: 'MOVIE', genre: '드라마');

      expect(filter.copyWith(sort: 'rating').genre, '드라마');
    });

    test('clearGenre 로만 장르를 지운다', () {
      const filter = BrowseFilter(type: 'MOVIE', genre: '드라마');

      expect(filter.copyWith(clearGenre: true).genre, isNull);
    });
  });

  group('toQuery', () {
    test('기본값과 쪽 번호를 붙인다', () {
      const filter = BrowseFilter(type: 'BOOK');

      expect(
        filter.toQuery(page: 2),
        '?type=BOOK&sort=popular&order=desc&page=2&size=$pageSize',
      );
    });

    test('한글 장르는 인코딩한다', () {
      const filter = BrowseFilter(type: 'MOVIE', genre: '드라마');

      expect(
        filter.toQuery(page: 1),
        contains('genre=%EB%93%9C%EB%9D%BC%EB%A7%88'),
      );
    });

    test('안 본 것만은 켰을 때만 보낸다', () {
      const off = BrowseFilter(type: 'MOVIE');
      final on = off.copyWith(unseen: true);

      expect(off.toQuery(page: 1), isNot(contains('unseen')));
      expect(on.toQuery(page: 1), contains('unseen=true'));
    });
  });
}
