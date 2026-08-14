"use client";

import { useLayoutEffect, useRef, useState } from "react";

/** 2줄에서 자른다. 넘칠 때만 더 보기가 붙는다 */
export default function MemoText({ text }: { text: string }) {
  const ref = useRef<HTMLParagraphElement>(null);
  const [clamped, setClamped] = useState(true);
  const [overflows, setOverflows] = useState(false);

  // 실제로 잘렸을 때만 버튼을 띄운다
  useLayoutEffect(() => {
    const el = ref.current;
    if (el) setOverflows(el.scrollHeight > el.clientHeight + 1);
  }, [text]);

  return (
    <>
      <p
        ref={ref}
        className={`mt-0.5 text-sm leading-6 whitespace-pre-wrap ${clamped ? "line-clamp-2" : ""}`}
      >
        {text}
      </p>
      {overflows && (
        <button
          type="button"
          onClick={() => setClamped((v) => !v)}
          className="mt-0.5 text-[12px] text-muted underline"
        >
          {clamped ? "더 보기" : "접기"}
        </button>
      )}
    </>
  );
}
