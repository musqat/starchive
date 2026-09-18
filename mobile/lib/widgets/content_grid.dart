import 'package:flutter/material.dart';

import '../models/content.dart';
import '../screens/detail_screen.dart';
import 'rating_badge.dart';

/// 포스터 격자. 목록과 보관함이 같이 쓴다
class ContentGrid extends StatelessWidget {
  const ContentGrid({super.key, required this.items, this.controller});

  final List<Content> items;

  /// 다음 쪽을 부르는 화면만 넘긴다
  final ScrollController? controller;

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      controller: controller,
      padding: const EdgeInsets.all(12),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        childAspectRatio: 0.52,
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
      ),
      itemCount: items.length,
      itemBuilder: (context, i) => ContentCard(item: items[i]),
    );
  }
}

class ContentCard extends StatelessWidget {
  const ContentCard({super.key, required this.item});

  final Content item;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.of(
        context,
      ).push(MaterialPageRoute(builder: (_) => DetailScreen(id: item.id))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  if (item.imageUrl == null)
                    ColoredBox(
                      color: Theme.of(
                        context,
                      ).colorScheme.surfaceContainerHighest,
                    )
                  else
                    Image.network(
                      item.imageUrl!,
                      fit: BoxFit.cover,
                      width: double.infinity,
                      errorBuilder: (context, _, _) => ColoredBox(
                        color: Theme.of(
                          context,
                        ).colorScheme.surfaceContainerHighest,
                      ),
                    ),
                  if (item.externalRating != null)
                    Positioned(
                      left: 4,
                      bottom: 4,
                      child: RatingBadge(rating: item.externalRating!),
                    ),
                  if (item.myRating != null)
                    Positioned(
                      right: 4,
                      top: 4,
                      child: RatingBadge(rating: item.myRating!, mine: true),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            item.title,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
