import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/content_detail.dart';
import '../providers/record_provider.dart';

/// 내 메모. 없으면 입력칸, 있으면 읽기 화면에 수정·삭제
class MemoSection extends ConsumerStatefulWidget {
  const MemoSection({super.key, required this.item});

  final ContentDetail item;

  @override
  ConsumerState<MemoSection> createState() => _MemoSectionState();
}

class _MemoSectionState extends ConsumerState<MemoSection> {
  late final TextEditingController _memo = TextEditingController(
    text: widget.item.myMemo ?? '',
  );
  late bool _public = widget.item.myMemoPublic;
  bool _editing = false;
  bool _saving = false;

  @override
  void dispose() {
    _memo.dispose();
    super.dispose();
  }

  /// 메모를 비워 보내면 서버가 지운다
  Future<void> _send(String memo, bool public) async {
    setState(() => _saving = true);

    String? error;
    try {
      await ref.read(recordControllerProvider).save(widget.item.id, {
        'memo': memo,
        'memo_public': public,
      });
    } on ApiException catch (e) {
      error = e.message;
    } catch (_) {
      error = '저장하지 못했어요';
    }

    if (!mounted) return;
    setState(() {
      _saving = false;
      if (error == null) _editing = false;
    });
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? '저장했어요')));
  }

  void _startEdit() {
    setState(() {
      _memo.text = widget.item.myMemo ?? '';
      _public = widget.item.myMemoPublic;
      _editing = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    final saved = widget.item.myMemo;
    if (saved == null || _editing) {
      return _form(context, canCancel: saved != null);
    }
    return _saved(context, saved);
  }

  Widget _form(BuildContext context, {required bool canCancel}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _memo,
          maxLines: 3,
          maxLength: 500,
          decoration: const InputDecoration(
            labelText: '메모',
            hintText: '감상을 적어 두면 나중에 찾기 쉬워요',
          ),
        ),
        Row(
          children: [
            Switch(
              value: _public,
              onChanged: (next) => setState(() => _public = next),
            ),
            const Text('공개'),
            const Spacer(),
            if (canCancel)
              TextButton(
                onPressed: _saving
                    ? null
                    : () => setState(() => _editing = false),
                child: const Text('취소'),
              ),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: _saving
                  ? null
                  : () => _send(_memo.text.trim(), _public),
              child: Text(_saving ? '저장 중' : '저장'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _saved(BuildContext context, String memo) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              widget.item.myMemoPublic ? '내 메모 · 공개' : '내 메모 · 나만 보기',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const Spacer(),
            TextButton(
              onPressed: _saving ? null : _startEdit,
              child: const Text('수정'),
            ),
            TextButton(
              onPressed: _saving
                  ? null
                  : () => _send('', widget.item.myMemoPublic),
              child: const Text('삭제'),
            ),
          ],
        ),
        Text(memo),
      ],
    );
  }
}
