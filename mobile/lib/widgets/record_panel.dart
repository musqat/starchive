import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/content_detail.dart';
import '../providers/record_provider.dart';

const _statuses = {'WISH': '보고싶어요', 'DOING': '보는 중', 'DONE': '봤어요'};

/// 상태·별점·좋아요·추천. 로그인한 사람에게만 보인다
class RecordPanel extends ConsumerWidget {
  const RecordPanel({super.key, required this.item});

  final ContentDetail item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final controller = ref.read(recordControllerProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          children: [
            for (final entry in _statuses.entries)
              ChoiceChip(
                label: Text(entry.value),
                selected: item.myStatus == entry.key,
                onSelected: (_) =>
                    controller.save(item.id, {'status': entry.key}),
              ),
          ],
        ),
        const SizedBox(height: 12),
        _Stars(
          value: item.myRating,
          onChange: (next) => controller.save(item.id, {'rating': next}),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          children: [
            FilterChip(
              label: const Text('좋아요'),
              selected: item.myLiked,
              onSelected: (next) => controller.save(item.id, {'liked': next}),
            ),
            FilterChip(
              label: const Text('추천해요'),
              selected: item.myRecommended,
              onSelected: (next) =>
                  controller.save(item.id, {'recommended': next}),
            ),
            if (item.myStatus != null)
              ActionChip(
                label: const Text('기록 지우기'),
                onPressed: () => controller.remove(item.id),
              ),
          ],
        ),
      ],
    );
  }
}

/// 0.5 단위 별점. 별 하나를 왼쪽·오른쪽으로 나눠 누른다
class _Stars extends StatelessWidget {
  const _Stars({required this.onChange, this.value});

  final double? value;
  final void Function(double?) onChange;

  @override
  Widget build(BuildContext context) {
    final current = value ?? 0;

    return Row(
      children: [
        for (var i = 0; i < 5; i++) _star(context, i, current),
        const SizedBox(width: 8),
        if (value != null)
          TextButton(
            onPressed: () => onChange(null),
            child: const Text('별점 지우기'),
          ),
      ],
    );
  }

  Widget _star(BuildContext context, int index, double current) {
    final full = index + 1.0;
    final half = index + 0.5;
    final icon = current >= full
        ? Icons.star
        : current >= half
        ? Icons.star_half
        : Icons.star_border;

    return SizedBox(
      width: 36,
      height: 36,
      child: Stack(
        children: [
          Center(child: Icon(icon, size: 32)),
          Row(
            children: [
              // 왼쪽 절반을 누르면 0.5, 오른쪽을 누르면 1.0
              Expanded(
                child: GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () => onChange(half),
                ),
              ),
              Expanded(
                child: GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () => onChange(full),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
