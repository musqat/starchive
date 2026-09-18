import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/auth_provider.dart';
import '../providers/browse_provider.dart';
import '../widgets/content_grid.dart';

const _sorts = {'popular': '인기순', 'rating': '평점순', 'recent': '최신순'};

class BrowseScreen extends ConsumerStatefulWidget {
  const BrowseScreen({super.key, required this.type, required this.title});

  final String type; // MOVIE / BOOK
  final String title;

  @override
  ConsumerState<BrowseScreen> createState() => _BrowseScreenState();
}

class _BrowseScreenState extends ConsumerState<BrowseScreen> {
  late BrowseFilter _filter = BrowseFilter(type: widget.type);
  final _scroll = ScrollController();

  @override
  void initState() {
    super.initState();
    _scroll.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  void _onScroll() {
    // 끝에서 300 픽셀 남았을 때 다음 쪽을 부른다
    final near =
        _scroll.position.pixels >= _scroll.position.maxScrollExtent - 300;
    if (near) ref.read(browseProvider(_filter).notifier).loadMore();
  }

  @override
  Widget build(BuildContext context) {
    final items = ref.watch(browseProvider(_filter));
    final genres = ref.watch(genresProvider(widget.type));
    final signedIn = ref.watch(authProvider).value != null;

    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                for (final entry in _sorts.entries)
                  Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: ChoiceChip(
                      label: Text(entry.value),
                      selected: _filter.sort == entry.key,
                      onSelected: (_) => setState(
                        () => _filter = _filter.copyWith(sort: entry.key),
                      ),
                    ),
                  ),
                if (signedIn)
                  Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: FilterChip(
                      label: const Text('안 본 것만'),
                      selected: _filter.unseen,
                      onSelected: (next) => setState(
                        () => _filter = _filter.copyWith(unseen: next),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          genres.maybeWhen(
            data: (list) => _GenreBar(
              genres: list,
              selected: _filter.genre,
              onSelect: (genre) => setState(() {
                _filter = genre == null
                    ? _filter.copyWith(clearGenre: true)
                    : _filter.copyWith(genre: genre);
              }),
            ),
            orElse: () => const SizedBox.shrink(),
          ),
          Expanded(
            child: items.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => const Center(child: Text('불러오지 못했어요')),
              data: (list) {
                if (list.isEmpty) {
                  return const Center(child: Text('조건에 맞는 작품이 없어요'));
                }
                return ContentGrid(items: list, controller: _scroll);
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _GenreBar extends StatelessWidget {
  const _GenreBar({
    required this.genres,
    required this.onSelect,
    this.selected,
  });

  final List<String> genres;
  final String? selected;
  final void Function(String?) onSelect;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 44,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        children: [
          Padding(
            padding: const EdgeInsets.only(right: 6),
            child: ChoiceChip(
              label: const Text('전체'),
              selected: selected == null,
              onSelected: (_) => onSelect(null),
            ),
          ),
          for (final genre in genres)
            Padding(
              padding: const EdgeInsets.only(right: 6),
              child: ChoiceChip(
                label: Text(genre),
                selected: selected == genre,
                onSelected: (_) => onSelect(genre),
              ),
            ),
        ],
      ),
    );
  }
}
