import 'package:flutter/material.dart';

import '../models/content.dart';
import '../screens/detail_screen.dart';

/// 제목 한 줄 + 가로로 넘기는 카드 목록
class ContentRow extends StatelessWidget {
  const ContentRow({
    super.key,
    required this.title,
    required this.items,
    this.empty,
  });

  final String title;
  final List<Content> items;

  /// 목록이 비었을 때 자리에 넣을 위젯
  final Widget? empty;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Text(title, style: Theme.of(context).textTheme.titleMedium),
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
              child: item.imageUrl == null
                  ? Container(
                      height: 160,
                      color: Theme.of(
                        context,
                      ).colorScheme.surfaceContainerHighest,
                    )
                  : Image.network(
                      item.imageUrl!,
                      height: 160,
                      width: 110,
                      fit: BoxFit.cover,
                      errorBuilder: (context, _, _) => Container(
                        height: 160,
                        color: Theme.of(
                          context,
                        ).colorScheme.surfaceContainerHighest,
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
