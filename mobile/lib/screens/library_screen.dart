import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/library_item.dart';
import '../providers/library_provider.dart';
import '../widgets/content_grid.dart';
import 'detail_screen.dart';

class LibraryScreen extends ConsumerStatefulWidget {
  const LibraryScreen({super.key});

  @override
  ConsumerState<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends ConsumerState<LibraryScreen> {
  LibraryTab _tab = LibraryTab.all;

  @override
  Widget build(BuildContext context) {
    final items = ref.watch(libraryProvider(_tab));

    return Scaffold(
      appBar: AppBar(title: const Text('보관함')),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                for (final tab in LibraryTab.values)
                  Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: ChoiceChip(
                      label: Text(tab.label),
                      selected: _tab == tab,
                      onSelected: (_) => setState(() => _tab = tab),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: items.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) =>
                  _Retry(onRetry: () => ref.invalidate(libraryProvider(_tab))),
              data: (list) {
                if (list.isEmpty) {
                  return const Center(child: Text('아직 기록이 없어요'));
                }
                return RefreshIndicator(
                  onRefresh: () async => ref.invalidate(libraryProvider(_tab)),
                  // 댓글 탭만 목록이다. 포스터만 깔면 정작 메모가 안 보인다
                  child: _tab == LibraryTab.memo
                      ? _MemoList(items: list)
                      : ContentGrid(items: list.map((e) => e.content).toList()),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

/// 실패했을 때 다시 시도
class _Retry extends StatelessWidget {
  const _Retry({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('불러오지 못했어요'),
          const SizedBox(height: 8),
          FilledButton(onPressed: onRetry, child: const Text('다시 시도')),
        ],
      ),
    );
  }
}

class _MemoList extends StatelessWidget {
  const _MemoList({required this.items});

  final List<LibraryItem> items;

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount: items.length,
      itemBuilder: (context, i) => _MemoTile(item: items[i]),
    );
  }
}

class _MemoTile extends StatelessWidget {
  const _MemoTile({required this.item});

  final LibraryItem item;

  @override
  Widget build(BuildContext context) {
    final content = item.content;
    final muted = Theme.of(context).textTheme.bodySmall;

    return InkWell(
      onTap: () => Navigator.of(
        context,
      ).push(MaterialPageRoute(builder: (_) => DetailScreen(id: content.id))),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: SizedBox(
                width: 56,
                height: 84,
                child: content.imageUrl == null
                    ? ColoredBox(
                        color: Theme.of(
                          context,
                        ).colorScheme.surfaceContainerHighest,
                      )
                    : Image.network(
                        content.imageUrl!,
                        fit: BoxFit.cover,
                        errorBuilder: (context, _, _) => ColoredBox(
                          color: Theme.of(
                            context,
                          ).colorScheme.surfaceContainerHighest,
                        ),
                      ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          content.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (item.rating != null) ...[
                        const SizedBox(width: 6),
                        Text(
                          '★ ${item.rating!.toStringAsFixed(1)}',
                          style: muted,
                        ),
                      ],
                      if (item.memoPublic) ...[
                        const SizedBox(width: 6),
                        const _PublicBadge(),
                      ],
                    ],
                  ),
                  const SizedBox(height: 4),
                  // 목록이라 두 줄까지. 전체는 눌러 들어가서 본다
                  Text(
                    item.memo ?? '',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: muted,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PublicBadge extends StatelessWidget {
  const _PublicBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text('공개', style: Theme.of(context).textTheme.labelSmall),
    );
  }
}
