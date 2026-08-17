import Link from "next/link";

import type { ContentType } from "@/lib/types";

const LABEL: Record<string, { unit: string; browse: string; href: string }> = {
  MOVIE: { unit: "영화", browse: "영화 둘러보기", href: "/movies" },
  BOOK: { unit: "책", browse: "책 둘러보기", href: "/books" },
};

export default function RecommendationEmpty({
  type,
  rated,
  required,
  action,
}: {
  type: ContentType;
  rated: number;
  required: number;
  /** 기록이 충분할 때 자리에 들어갈 버튼 */
  action?: React.ReactNode;
}) {
  const label = LABEL[type] ?? LABEL.MOVIE;
  const enough = rated >= required;

  return (
    <div className="flex flex-col items-start justify-between gap-4 rounded-xl border border-dashed border-line p-5 sm:flex-row sm:items-center">
      <div>
        {enough ? (
          <>
            <p className="text-[13px]">기록 {rated}편으로 추천을 만들 수 있어요</p>
            <p className="mt-1 text-[11px] text-muted">몇 초 걸려요</p>
          </>
        ) : (
          <>
            <p className="text-[13px]">
              {label.unit} {required}편을 평가하면 추천을 만들어드려요
            </p>
            <div className="mt-2 flex items-center gap-1.5">
              {Array.from({ length: required }, (_, i) => (
                <span
                  key={i}
                  className={`h-[3px] w-5 rounded-sm ${i < rated ? "bg-foreground" : "bg-line"}`}
                />
              ))}
              <span className="ml-1.5 text-[11px] text-muted">
                {rated} / {required}
              </span>
            </div>
          </>
        )}
      </div>

      {enough ? (
        action
      ) : (
        <Link
          href={label.href}
          className="shrink-0 rounded-lg border border-line px-4 py-[7px] text-[13px]"
        >
          {label.browse}
        </Link>
      )}
    </div>
  );
}
