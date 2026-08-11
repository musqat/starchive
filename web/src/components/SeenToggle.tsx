"use client";

import { useSyncExternalStore } from "react";

const KEY = "starchive:seen";
const CHANGED = "starchive:seen-change";

function read(): string[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

function subscribe(onChange: () => void) {
  window.addEventListener(CHANGED, onChange);
  window.addEventListener("storage", onChange); // 다른 탭에서 바뀐 경우
  return () => {
    window.removeEventListener(CHANGED, onChange);
    window.removeEventListener("storage", onChange);
  };
}

export default function SeenToggle({ id, label }: { id: string; label: string }) {
  // 서버는 localStorage 를 모름. 세 번째 인자가 서버 스냅샷이라 하이드레이션 불일치 방지
  const seen = useSyncExternalStore(
    subscribe,
    () => read().includes(id),
    () => false,
  );

  function toggle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();

    const next = seen ? read().filter((x) => x !== id) : [...read(), id];
    localStorage.setItem(KEY, JSON.stringify(next));
    // 같은 항목이 여러 줄에 나올 수 있어서 모든 카드를 함께 갱신
    window.dispatchEvent(new Event(CHANGED));
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={seen}
      aria-label={`${label} ${seen ? "안 본 것으로" : "본 것으로"} 표시`}
      className={`absolute right-1.5 top-1.5 z-10 grid h-7 w-7 place-items-center rounded-full text-sm transition ${
        seen
          ? "bg-white text-black"
          : "bg-black/50 text-white/70 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
      }`}
    >
      ✓
    </button>
  );
}
