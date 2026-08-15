"use client";

import { useState } from "react";

/** 0.5 단위 별점. 표시 혹은 입력 */
export default function Stars({
  value,
  onChange,
  size = 20,
  label,
}: {
  value: number | null;
  /** 없으면 읽기 전용 */
  onChange?: (next: number) => void;
  size?: number;
  /** 입력용일 때 버튼 이름 앞에 붙는다. 목록에서 구분 용 */
  label?: string;
}) {
  const [hovered, setHovered] = useState<number | null>(null);

  // 마우스를 호버하면 그 값을 미리 보여준다.
  const shown = hovered ?? value ?? 0;
  const filled = `${(shown / 5) * 100}%`;

  return (
    <div
      className="relative w-fit"
      onMouseLeave={() => setHovered(null)}
      style={{ fontSize: size, lineHeight: 1 }}
    >
      <div className="flex text-white/25">★★★★★</div>

      {/* gap 을 주면 잘리는 위치가 어긋난다. 붙여서 그린다 */}
      <div
        className={`absolute inset-0 overflow-hidden ${
          hovered === null ? "text-amber-400" : "text-amber-400/70"
        }`}
        style={{ width: filled }}
      >
        <div className="flex">★★★★★</div>
      </div>

      {onChange && (
        <div className="absolute inset-0 flex">
          {HALVES.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => onChange(n)}
              onMouseEnter={() => setHovered(n)}
              aria-label={label ? `${label} ${n}점` : `${n}점`}
              aria-pressed={value === n}
              className="h-full flex-1"
            />
          ))}
        </div>
      )}
    </div>
  );
}

const HALVES = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5];
