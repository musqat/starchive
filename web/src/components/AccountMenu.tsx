"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { logOut } from "@/lib/client";

const ITEM =
  "block w-full px-3 py-2 text-left text-[13px] text-muted transition hover:bg-fill hover:text-foreground";

export default function AccountMenu({ nickname }: { nickname: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function onDocumentClick(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onDocumentClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocumentClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function handleLogOut() {
    await logOut();
    // 서버 컴포넌트가 쿠키를 다시 읽도록 전체 새로고침
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign("/");
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="내 계정"
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex items-center gap-1 text-sm transition hover:text-foreground"
      >
        {nickname}
        <span aria-hidden className="text-[10px] text-muted">
          ▾
        </span>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-2 w-36 overflow-hidden rounded-lg border border-line bg-background py-1 shadow-xl"
        >
          <Link href="/account" role="menuitem" onClick={() => setOpen(false)} className={ITEM}>
            마이페이지
          </Link>
          <button type="button" role="menuitem" onClick={handleLogOut} className={ITEM}>
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
}
