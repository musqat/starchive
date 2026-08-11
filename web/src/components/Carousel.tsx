"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export default function Carousel({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLUListElement>(null);
  const [atStart, setAtStart] = useState(true);
  const [atEnd, setAtEnd] = useState(true);

  const sync = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    setAtStart(el.scrollLeft <= 8);
    setAtEnd(el.scrollLeft + el.clientWidth >= el.scrollWidth - 8);
  }, []);

  useEffect(() => {
    sync();
    window.addEventListener("resize", sync);
    return () => window.removeEventListener("resize", sync);
  }, [sync]);

  function scroll(direction: 1 | -1) {
    const el = ref.current;
    if (!el) return;
    // 화면 폭의 80%씩. 다음 화면과 겹쳐야 위치를 잃지 않음
    el.scrollBy({ left: direction * el.clientWidth * 0.8, behavior: "smooth" });
  }

  return (
    <div className="group/carousel relative">
      <ul
        ref={ref}
        onScroll={sync}
        className="-mx-4 flex snap-x snap-mandatory scroll-px-4 gap-3 overflow-x-auto px-4 pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {children}
      </ul>

      <Arrow side="left" hidden={atStart} onClick={() => scroll(-1)} />
      <Arrow side="right" hidden={atEnd} onClick={() => scroll(1)} />
    </div>
  );
}

function Arrow({
  side,
  hidden,
  onClick,
}: {
  side: "left" | "right";
  hidden: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={side === "left" ? "이전" : "다음"}
      className={`absolute top-[38%] z-10 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-full bg-background/80 text-sm backdrop-blur transition ${
        side === "left" ? "-left-2" : "-right-2"
      } ${
        hidden
          ? "pointer-events-none opacity-0"
          : "opacity-0 group-hover/carousel:opacity-100 focus-visible:opacity-100"
      }`}
    >
      {side === "left" ? "‹" : "›"}
    </button>
  );
}
