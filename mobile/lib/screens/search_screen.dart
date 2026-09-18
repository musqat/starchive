import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/content.dart';
import '../providers/search_provider.dart';
import 'detail_screen.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _input = TextEditingController();

  /// 실제로 부른 검색어. 입력 중에는 안 바뀐다
  String _query = '';

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  void _search() {
    setState(() {
      _query = _input.text.trim();
    });
  }

  @override
  Widget build(BuildContext context) {
    final result = ref.watch(searchProvider(_query));

    return Scaffold(
      appBar: AppBar(title: const Text('검색')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _input,
              autofocus: true,
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => _search(),
              decoration: InputDecoration(
                hintText: '제목·감독·배우, 또는 분위기로',
                suffixIcon: IconButton(
                  onPressed: _search,
                  icon: const Icon(Icons.search),
                ),
              ),
            ),
          ),
          Expanded(
            child: result.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(
                child: Text(
                  e is ApiException ? e.message : '검색하지 못했어요',
                  textAlign: TextAlign.center,
                ),
              ),
              data: (data) {
                if (data == null) {
                  return const Center(child: Text('검색어를 넣어 보세요'));
                }
                if (data.items.isEmpty) {
                  return const Center(child: Text('찾은 게 없어요'));
                }
                return ListView(
                  children: [
                    if (data.comment != null)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                        child: Text(
                          data.comment!,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ),
                    for (final item in data.items) _ResultTile(item: item),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ResultTile extends StatelessWidget {
  const _ResultTile({required this.item});

  final Content item;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: SizedBox(
        width: 48,
        height: 68,
        child: item.imageUrl == null
            ? ColoredBox(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
              )
            : Image.network(
                item.imageUrl!,
                fit: BoxFit.cover,
                errorBuilder: (context, _, _) => ColoredBox(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                ),
              ),
      ),
      title: Text(item.title, maxLines: 2, overflow: TextOverflow.ellipsis),
      subtitle: Text(item.creator ?? (item.type == 'MOVIE' ? '영화' : '책')),
      onTap: () => Navigator.of(
        context,
      ).push(MaterialPageRoute(builder: (_) => DetailScreen(id: item.id))),
    );
  }
}
