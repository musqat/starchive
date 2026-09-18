import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/content.dart';
import '../models/recommendation.dart';
import '../models/user.dart';
import '../providers/auth_provider.dart';
import '../providers/content_provider.dart';
import '../widgets/content_row.dart';
import 'account_screen.dart';
import 'login_screen.dart';
import 'browse_screen.dart';
import 'library_screen.dart';
import 'search_screen.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key, required this.user});

  /// null 이면 로그인 전. 인기 목록만 보여 준다
  final User? user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: Text(user == null ? 'starchive' : '${user!.nickname} 님'),
        actions: [
          IconButton(
            onPressed: () => Navigator.of(
              context,
            ).push(MaterialPageRoute(builder: (_) => const SearchScreen())),
            icon: const Icon(Icons.search),
            tooltip: '검색',
          ),
          if (user != null)
            IconButton(
              onPressed: () => Navigator.of(
                context,
              ).push(MaterialPageRoute(builder: (_) => const LibraryScreen())),
              icon: const Icon(Icons.bookmark_border),
              tooltip: '보관함',
            ),
          if (user != null)
            IconButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => AccountScreen(user: user!)),
              ),
              icon: const Icon(Icons.person_outline),
              tooltip: '계정',
            ),
          if (user == null)
            TextButton(
              onPressed: () => Navigator.of(
                context,
              ).push(MaterialPageRoute(builder: (_) => const LoginScreen())),
              child: const Text('로그인'),
            )
          else
            IconButton(
              onPressed: () => ref.read(authProvider.notifier).logout(),
              icon: const Icon(Icons.logout),
              tooltip: '로그아웃',
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(popularProvider);
          ref.invalidate(recommendationsProvider);
        },
        child: ListView(
          children: [
            // 추천은 로그인한 사람에게만 나간다
            if (user != null) ...[
              const _RecommendationRow(title: '당신을 위한 영화', type: 'MOVIE'),
              const _RecommendationRow(title: '당신을 위한 책', type: 'BOOK'),
            ],
            const _PopularRow(title: '인기 영화', type: 'MOVIE'),
            const _PopularRow(title: '인기 책', type: 'BOOK'),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

class _PopularRow extends ConsumerWidget {
  const _PopularRow({required this.title, required this.type});

  final String title;
  final String type;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(popularProvider(type));
    return items.when(
      loading: () => _Loading(title: title),
      error: (e, _) => _Failed(title: title),
      data: (list) => ContentRow(
        title: title,
        items: list,
        onMore: () => Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => BrowseScreen(type: type, title: title),
          ),
        ),
      ),
    );
  }
}

class _RecommendationRow extends ConsumerWidget {
  const _RecommendationRow({required this.title, required this.type});

  final String title;
  final String type;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recommendations = ref.watch(recommendationsProvider(type));
    return recommendations.when(
      loading: () => _Loading(title: title),
      error: (e, _) => _Failed(title: title),
      data: (list) => ContentRow(
        title: title,
        items: _contents(list),
        empty: Text(_guide(list)),
      ),
    );
  }

  List<Content> _contents(RecommendationList list) {
    return list.items.map((r) => r.content).toList();
  }

  String _guide(RecommendationList list) {
    final rating = list.requiredRating.toStringAsFixed(1);
    return '★$rating 이상 ${list.remaining}편을 더 기록하면 추천이 열려요';
  }
}

class _Loading extends StatelessWidget {
  const _Loading({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return ContentRow(
      title: title,
      items: const [],
      empty: const Padding(
        padding: EdgeInsets.symmetric(vertical: 8),
        child: SizedBox(
          height: 24,
          width: 24,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
    );
  }
}

class _Failed extends StatelessWidget {
  const _Failed({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return ContentRow(
      title: title,
      items: const [],
      empty: const Text('불러오지 못했어요'),
    );
  }
}
