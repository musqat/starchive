"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Drawer({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") router.back();
    }
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [router]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex justify-end"
      onClick={() => router.back()}
    >
      <div className="absolute inset-0 bg-black/60" />
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative h-full w-full max-w-xl overflow-y-auto border-l border-line bg-background p-6 shadow-2xl"
      >
        <button
          type="button"
          onClick={() => router.back()}
          aria-label="닫기"
          className="mb-4 grid h-8 w-8 place-items-center rounded-full bg-fill text-muted"
        >
          ✕
        </button>
        {children}
      </div>
    </div>
  );
}
