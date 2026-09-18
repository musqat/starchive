import 'package:flutter/material.dart';

/// 포스터 위에 얹는 평점. 어두운 바탕이라 글자가 읽힌다
class RatingBadge extends StatelessWidget {
  const RatingBadge({super.key, required this.rating, this.mine = false});

  final double rating;

  /// 내가 준 별점이면 색을 달리해 외부 평점과 구분한다
  final bool mine;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: mine ? scheme.primary : Colors.black.withValues(alpha: 0.65),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        '★ ${rating.toStringAsFixed(1)}',
        style: TextStyle(
          color: mine ? scheme.onPrimary : Colors.white,
          fontSize: 11,
        ),
      ),
    );
  }
}
