import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/recommendation.dart';
import '../providers/recommendation_provider.dart';

/// 추천 줄 위에 붙는 머리. 만든 날짜와 다시 만들기 단추
class RefreshRecommendations extends ConsumerStatefulWidget {
  const RefreshRecommendations({super.key, required this.list});

  final RecommendationList list;

  @override
  ConsumerState<RefreshRecommendations> createState() =>
      _RefreshRecommendationsState();
}

class _RefreshRecommendationsState
    extends ConsumerState<RefreshRecommendations> {
  bool _running = false;

  Future<void> _run() async {
    setState(() => _running = true);

    String? error;
    try {
      await ref.read(recommendationControllerProvider).refresh();
    } on ApiException catch (e) {
      error = e.message;
    } catch (_) {
      error = '서버에 연결하지 못했어요';
    }

    if (!mounted) return;
    setState(() => _running = false);
    if (error != null) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(error)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final list = widget.list;
    // 기록이 모자라면 단추를 아예 안 보여 준다
    if (list.ratedCount < list.requiredCount) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 8, 0),
      child: Row(
        children: [
          if (list.generatedAt != null)
            Text(
              '${list.generatedAt!.month}월 ${list.generatedAt!.day}일 만듦',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          const Spacer(),
          TextButton(
            onPressed: _running ? null : _run,
            child: Text(_running ? '만드는 중' : '다시 만들기'),
          ),
        ],
      ),
    );
  }
}
