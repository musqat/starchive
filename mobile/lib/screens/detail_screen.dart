import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/content_detail.dart';
import '../providers/detail_provider.dart';

/// TMDB 로고는 경로 조각만 온다. 앞에 이 주소를 붙인다
const _tmdbLogoBase = 'https://image.tmdb.org/t/p/w92';

class DetailScreen extends ConsumerWidget {
  const DetailScreen({super.key, required this.id});

  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detail = ref.watch(detailProvider(id));

    return Scaffold(
      appBar: AppBar(),
      body: detail.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => const Center(child: Text('불러오지 못했어요')),
        data: (item) => _Body(item: item),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  const _Body({required this.item});

  final ContentDetail item;

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodySmall;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 32),
      children: [
        if (item.imageUrl != null)
          Center(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.network(item.imageUrl!, height: 260),
            ),
          ),
        const SizedBox(height: 16),
        Text(item.title, style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 8),
        Text(_subtitle(item), style: muted),
        if (item.genre.isNotEmpty) ...[
          const SizedBox(height: 12),
          Wrap(
            spacing: 6,
            children: [for (final g in item.genre) Chip(label: Text(g))],
          ),
        ],
        const SizedBox(height: 12),
        Text(_rating(item), style: muted),
        const SizedBox(height: 16),
        _WatchLinks(item: item),
        if (item.description != null) ...[
          const SizedBox(height: 16),
          Text(item.description!, style: const TextStyle(height: 1.7)),
        ],
      ],
    );
  }

  String _subtitle(ContentDetail item) {
    final runtime = item.runtime;
    final parts = [
      item.creator,
      item.releaseDate,
      if (runtime != null) '$runtime분',
    ].whereType<String>();
    return parts.join(' · ');
  }

  String _rating(ContentDetail item) {
    final rating = item.externalRating;
    final popularity = item.externalPopularity;
    final head = rating == null ? '평가 없음' : '★ ${rating.toStringAsFixed(1)}';
    return popularity == null ? head : '$head · $popularity명';
  }
}

/// 영화는 시청처 로고, 책은 알라딘 링크
class _WatchLinks extends StatelessWidget {
  const _WatchLinks({required this.item});

  final ContentDetail item;

  @override
  Widget build(BuildContext context) {
    final providers = item.metadata['providers'] as Map<String, dynamic>?;
    final items = providers?['items'] as List?;
    if (items == null || items.isEmpty) return const SizedBox.shrink();

    return Wrap(
      spacing: 8,
      children: [
        for (final p in items.cast<Map<String, dynamic>>())
          _ProviderLogo(
            name: p['name'] as String,
            logoPath: p['logo_path'] as String?,
          ),
      ],
    );
  }
}

class _ProviderLogo extends StatelessWidget {
  const _ProviderLogo({required this.name, this.logoPath});

  final String name;
  final String? logoPath;

  @override
  Widget build(BuildContext context) {
    if (logoPath == null) {
      return Chip(label: Text(name));
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(6),
      child: Image.network(
        '$_tmdbLogoBase$logoPath',
        width: 40,
        height: 40,
        errorBuilder: (context, _, _) => Chip(label: Text(name)),
      ),
    );
  }
}
