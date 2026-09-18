import 'package:flutter/material.dart';

/// 포스터 위에 얹는 평점. 어두운 바탕이라 글자가 읽힌다
class RatingBadge extends StatelessWidget {
  const RatingBadge({super.key, required this.rating});

  final double rating;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.65),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        '★ ${rating.toStringAsFixed(1)}',
        style: const TextStyle(color: Colors.white, fontSize: 11),
      ),
    );
  }
}
