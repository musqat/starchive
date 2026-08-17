"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { refreshRecommendations } from "@/lib/client";

export default function RefreshRecommendations({
  label = "다시 만들기",
  className = "",
}: {
  label?: string;
  className?: string;
}) {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // 서버 컴포넌트를 다시 그리는 동안도 버튼을 잠근다
  const [refreshing, startRefresh] = useTransition();
  const busy = running || refreshing;

  async function run() {
    setError(null);
    setRunning(true);
    try {
      await refreshRecommendations();
      startRefresh(() => router.refresh());
    } catch (e) {
      setError(e instanceof Error ? e.message : "잠시 뒤에 다시 시도해주세요");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className={`flex shrink-0 items-center gap-3 ${className}`}>
      {error && <span className="text-[11px] text-muted">{error}</span>}
      <button
        type="button"
        onClick={run}
        disabled={busy}
        className="rounded-lg border border-foreground/40 px-4 py-[7px] text-[13px] disabled:border-line disabled:text-muted"
      >
        {busy ? "만드는 중" : label}
      </button>
    </div>
  );
}
