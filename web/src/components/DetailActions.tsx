"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import Stars from "@/components/Stars";
import { deleteRecord, putRecord } from "@/lib/client";
import { statusLabel } from "@/lib/labels";
import type { ContentDetail, ContentStatus } from "@/lib/types";

type State = {
  status: ContentStatus | null;
  rating: number | null;
  liked: boolean;
  recommended: boolean;
};


/** 상세용. 별점과 상태를 함께 다룬다 */
export default function DetailActions({ item }: { item: ContentDetail }) {
  const [state, setState] = useState<State>({
    status: item.my_status,
    rating: item.my_rating,
    liked: item.my_liked,
    recommended: item.my_recommended,
  });
  const latest = useRef(state);
  const [needsLogin, setNeedsLogin] = useState(false);

  const seen = state.status === "DONE";

  function apply(next: (prev: State) => State) {
    const prev = latest.current;
    const value = next(prev);
    latest.current = value;
    setState(value);

    const request =
      value.status === null
        ? deleteRecord(item.id)
        : putRecord(item.id, value as { status: ContentStatus });

    request.catch((err) => {
      latest.current = prev;
      setState(prev);
      if (String(err).includes("not authorized")) setNeedsLogin(true);
    });
  }

  // 같은 별을 다시 누르면 평점을 지운다
  const rate = (n: number) =>
    apply((prev) => ({
      ...prev,
      rating: prev.rating === n ? null : n,
      status: "DONE",
    }));

  const toggleSeen = () =>
    apply((prev) =>
      prev.status === "DONE"
        ? { status: null, rating: null, liked: false, recommended: false }
        : { ...prev, status: "DONE" },
    );

  const toggleLiked = () =>
    apply((prev) => ({ ...prev, liked: !prev.liked, status: "DONE" }));

  const toggleRecommended = () =>
    apply((prev) => ({ ...prev, recommended: !prev.recommended, status: "DONE" }));

  return (
    <div className="mt-4 border-t border-line pt-3">
      <p className="mb-1 text-[11px] text-muted">내 평점</p>
      <div className="mb-3">
        <Stars value={state.rating} onChange={rate} size={22} />
      </div>

      <div className="grid gap-1.5">
        <Action active={seen} onClick={toggleSeen}>
          ✓ {statusLabel(item.type, "DONE")}
        </Action>
        {seen && (
          <>
            <Action active={state.liked} onClick={toggleLiked}>
              ♥ 좋아요
            </Action>
            <Action active={state.recommended} onClick={toggleRecommended}>
              👍 추천해요
            </Action>
          </>
        )}
      </div>

      {needsLogin && (
        <p className="mt-2 text-[12px] leading-snug text-muted">
          기록은 저장되지 않습니다.{" "}
          <Link href="/login" className="text-foreground underline">
            로그인
          </Link>
        </p>
      )}
    </div>
  );
}

function Action({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-lg py-1.5 text-[13px] transition ${
        active
          ? "bg-foreground text-background"
          : "bg-fill text-muted hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}
