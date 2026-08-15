"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import Stars from "@/components/Stars";
import { deleteRecord, putRecord } from "@/lib/client";
import { statusLabel } from "@/lib/labels";
import type { ContentStatus, ContentSummary } from "@/lib/types";

type State = {
  status: ContentStatus | null;
  rating: number | null;
  liked: boolean;
  recommended: boolean;
};


/** 카드용. 좌상단 별점, 우상단 봤어요. 추천은 상세에서 */
export default function StatusToggle({ item }: { item: ContentSummary }) {
  const [state, setState] = useState<State>({
    status: item.my_status,
    rating: item.my_rating,
    liked: item.my_liked,
    recommended: item.my_recommended,
  });
  const latest = useRef(state);
  const [needsLogin, setNeedsLogin] = useState(false);

  const seen = state.status === "DONE";

  /** 연속 클릭에서 낡은 값을 보지 않도록 ref 로 최신 상태를 들고 있는다 */
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

  /** 카드 전체가 Link 라 안쪽 클릭은 이동을 막아야 한다 */
  const stopNavigation = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  // 봤어요를 끄면 기록을 지운다. 안 본 것을 평가할 수 없다
  const toggleSeen = (e: React.MouseEvent) => {
    stopNavigation(e);
    apply((prev) =>
      prev.status === "DONE"
        ? { status: null, rating: null, liked: false, recommended: false }
        : { ...prev, status: "DONE" },
    );
  };

  // 같은 별을 다시 누르면 평점을 지운다
  const rate = (n: number) =>
    apply((prev) => ({ ...prev, rating: prev.rating === n ? null : n }));

  return (
    <>
      {seen && (
        // 평점이 없으면 hover 전까지 숨긴다. 빈 별은 포스터 위에서 잘 안 보인다
        <div
          onClick={stopNavigation}
          className={`absolute left-1.5 top-1.5 z-10 rounded-full bg-black/55 px-1.5 py-1 transition ${
            state.rating ? "" : "opacity-0 group-hover:opacity-100 focus-within:opacity-100"
          }`}
        >
          <Stars value={state.rating} onChange={rate} size={18} label={item.title} />
        </div>
      )}

      <Pill
        className="absolute right-1.5 top-1.5 z-10"
        active={seen}
        label={`${item.title} ${statusLabel(item.type, "DONE")}`}
        onClick={toggleSeen}
      >
        ✓
      </Pill>

      {needsLogin && (
        <p className="absolute inset-x-1.5 top-10 z-20 rounded-lg bg-black/85 px-2 py-1.5 text-[11px] leading-snug text-white">
          기록은 저장되지 않습니다.{" "}
          <Link href="/login" className="underline" onClick={(e) => e.stopPropagation()}>
            로그인
          </Link>
        </p>
      )}
    </>
  );
}

function Pill({
  children,
  active,
  label,
  onClick,
  className = "",
}: {
  children: React.ReactNode;
  active: boolean;
  label: string;
  onClick: (e: React.MouseEvent) => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      aria-label={label}
      className={`${className} grid h-7 w-7 place-items-center rounded-full text-xs transition ${
        active
          ? "bg-white text-black"
          : "bg-black/55 text-white/70 opacity-0 hover:bg-black/75 hover:text-white group-hover:opacity-100 focus-visible:opacity-100"
      }`}
    >
      {children}
    </button>
  );
}
