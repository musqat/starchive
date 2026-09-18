import 'package:flutter/material.dart';

import '../models/content.dart';
import '../screens/detail_screen.dart';
import 'rating_badge.dart';

/// 제목 한 줄 + 가로로 넘기는 카드 목록
class ContentRow extends StatelessWidget {
  const ContentRow({
    super.key,
    required this.title,
    required this.items,
    this.empty,
    this.onMore,
  });

  final String title;
  final List<Content> items;

  /// 목록이 비었을 때 자리에 넣을 위젯
  final Widget? empty;

  /// 있으면 제목 옆에 전체 보기가 생긴다
  final VoidCallback? onMore;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 8, 8),
          child: Row(
            children: [
              Text(title, style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              if (onMore != null)
                TextButton(onPressed: onMore, child: const Text('전체 보기')),
            ],
          ),
        ),
        if (items.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: empty ?? const Text('아직 없어요'),
          )
        else
          SizedBox(
            height: 210,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: items.length,
              separatorBuilder: (_, _) => const SizedBox(width: 12),
              itemBuilder: (context, i) => _Card(item: items[i]),
            ),
          ),
      ],
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.item});

  final Content item;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 110,
      child: InkWell(
        onTap: () => Navigator.of(
          context,
        ).push(MaterialPageRoute(builder: (_) => DetailScreen(id: item.id))),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: SizedBox(
                height: 160,
                width: 110,
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
      ),
    );
  }
}
