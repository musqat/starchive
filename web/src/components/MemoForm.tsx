"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { putRecord } from "@/lib/client";
import type { ContentDetail } from "@/lib/types";
import { useUnsaved } from "@/lib/unsaved";

const MAX = 500;

/** 상세의 내 메모. 공개로 켜면 닉네임·별점과 함께 남들에게 보인다 */
export default function MemoForm({ item }: { item: ContentDetail }) {
  const [memo, setMemo] = useState(item.my_memo ?? "");
  const [isPublic, setIsPublic] = useState(item.my_memo_public);
  const [stored, setStored] = useState(item.my_memo);
  const [storedPublic, setStoredPublic] = useState(item.my_memo_public);
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const text = memo.trim();
  // 내용 없이 공개만 켜면 빈 기록이 남는다
  const nothing = !text && !stored;
  // 저장된 값과 같으면 버튼을 잠근다
  const unchanged = memo === (stored ?? "") && isPublic === storedPublic;

  // 드로어를 닫거나 창을 떠날 때 확인을 받는다
  const setUnsaved = useUnsaved();
  useEffect(() => {
    setUnsaved(!unchanged && !nothing);
    return () => setUnsaved(false);
  }, [unchanged, nothing, setUnsaved]);

  useEffect(() => {
    if (unchanged || nothing) return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [unchanged, nothing]);

  async function send(next: string | null, message: string) {
    setSaved(null);
    setError(null);
    setPending(true);

    try {
      await putRecord(item.id, { memo: next, memo_public: isPublic });
      setStored(next);
      setStoredPublic(isPublic);
      setSaved(message);
    } catch (e) {
      const detail = e instanceof Error ? e.message : "요청에 실패했습니다";
      setError(detail.includes("not authorized") ? "로그인이 필요합니다" : detail);
    }
    setPending(false);
  }

  const save = () =>
    send(text || null, isPublic && text ? "저장했습니다. 다른 사람에게 보입니다" : "저장했습니다");

  function remove() {
    setMemo("");
    send(null, "지웠습니다");
  }

  return (
    <section className="mt-8 border-t border-line pt-5">
      <h2 className="mb-2 text-[13px] font-medium">내 댓글</h2>

      <textarea
        value={memo}
        onChange={(e) => setMemo(e.target.value.slice(0, MAX))}
        rows={3}
        placeholder="댓글을 작성해주세요"
        aria-label="내 댓글"
        className="w-full resize-y rounded-lg border border-line bg-fill px-3 py-2.5 text-sm transition
                   placeholder:text-muted hover:border-foreground/25
                   focus:border-foreground/50 focus:bg-transparent focus:outline-none"
      />

      <p className="mt-2 text-[11px] text-muted">공개 여부를 선택해주세요</p>

      <div className="mt-1 flex flex-wrap items-center gap-3">
        <label
          className={`flex items-center gap-1.5 text-[13px] ${nothing ? "text-muted/40" : "text-muted"}`}
        >
          <input
            type="checkbox"
            checked={isPublic}
            disabled={nothing}
            onChange={(e) => setIsPublic(e.target.checked)}
            className="accent-foreground disabled:cursor-not-allowed"
          />
          공개
        </label>

        <span className="text-[11px] text-muted">
          {memo.length} / {MAX}
        </span>

        <div className="ml-auto flex gap-2">
          {stored && (
            <button
              type="button"
              onClick={remove}
              disabled={pending}
              className="rounded-lg px-3 py-1.5 text-[13px] text-muted transition
                         hover:text-red-400 disabled:cursor-not-allowed disabled:opacity-40"
            >
              삭제
            </button>
          )}
          <button
            type="button"
            onClick={save}
            disabled={pending || unchanged || nothing}
            className="rounded-lg bg-foreground px-3 py-1.5 text-[13px] font-medium text-background transition
                       hover:bg-foreground/85 active:scale-[0.99]
                       disabled:cursor-not-allowed disabled:opacity-40"
          >
            {pending ? "저장 중…" : "저장"}
          </button>
        </div>
      </div>

      {saved && <p className="mt-2 text-[12px] text-muted">{saved}</p>}
      {error && (
        <p role="alert" className="mt-2 text-[12px] text-red-400">
          {error}{" "}
          <Link href="/login" className="underline">
            로그인
          </Link>
        </p>
      )}
    </section>
  );
}
