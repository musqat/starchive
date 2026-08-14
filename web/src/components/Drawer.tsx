"use client";

import { useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

import { UnsavedContext } from "@/lib/unsaved";

export default function Drawer({
  children,
  pagePath,
}: {
  children: React.ReactNode;
  /** 같은 내용의 단독 페이지 주소 */
  pagePath: string;
}) {
  const router = useRouter();

  // 메모를 쓰다가 배경을 잘못 눌러 날리는 일이 없도록 한 번 묻는다
  const dirty = useRef(false);
  const setDirty = useCallback((value: boolean) => {
    dirty.current = value;
  }, []);

  const close = useCallback(() => {
    if (dirty.current && !window.confirm("저장하지 않은 댓글이 있습니다. 닫을까요?")) return;
    router.back();
  }, [router]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") close();
    }
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [close]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex justify-end"
      onClick={close}
    >
      <div className="absolute inset-0 bg-black/60" />
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative h-full w-full overflow-y-auto border-l border-line bg-background p-6 shadow-2xl sm:w-[75vw] sm:max-w-5xl"
      >
        <div className="mb-4 flex items-center gap-2">
          <button
            type="button"
            onClick={close}
            aria-label="닫기"
            className="grid h-8 w-8 place-items-center rounded-full bg-fill text-muted transition hover:text-foreground"
          >
            ✕
          </button>
          {/* Link 로 가면 인터셉트가 다시 걸려 드로어가 그대로다. 전체 이동이어야 한다 */}
          <a
            href={pagePath}
            aria-label="페이지로 열기"
            title="페이지로 열기"
            className="grid h-8 w-8 place-items-center rounded-full bg-fill text-sm text-muted transition hover:text-foreground"
          >
            ↗
          </a>
        </div>

        <UnsavedContext.Provider value={setDirty}>{children}</UnsavedContext.Provider>
      </div>
    </div>
  );
}
