import Link from "next/link";

import type { SortKey, SortOrder } from "@/lib/types";

const SORTS: { key: SortKey; label: string }[] = [
  { key: "popular", label: "인기순" },
  { key: "rating", label: "평점순" },
  { key: "recent", label: "최신순" },
];

const MAX_GENRES = 12;

function href(basePath: string, params: Record<string, string | undefined>) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) q.set(k, v);
  }
  const s = q.toString();
  return s ? `${basePath}?${s}` : basePath;
}

function Chip({
  to,
  active,
  children,
}: {
  to: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={to}
      className={`rounded-full px-3 py-1 text-[13px] whitespace-nowrap ${
        active ? "bg-foreground text-background" : "bg-fill text-muted"
      }`}
    >
      {children}
    </Link>
  );
}

export default function Filters({
  basePath,
  genres,
  genre,
  sort,
  order,
}: {
  basePath: string;
  genres: string[];
  genre?: string;
  sort: SortKey;
  order: SortOrder;
}) {
  // 선택된 장르가 상위 12개 밖이면 목록에 추가
  const shown = genres.slice(0, MAX_GENRES);
  if (genre && !shown.includes(genre)) shown.push(genre);

  // 기본값(popular / desc)은 URL 에서 생략
  const keep = {
    genre,
    sort: sort === "popular" ? undefined : sort,
    order: order === "desc" ? undefined : order,
  };

  return (
    <div className="mb-5 space-y-3">
      <div className="flex flex-wrap gap-2">
        {SORTS.map((s) => {
          const active = sort === s.key;
          // 이미 선택된 정렬을 다시 누르면 방향 반전
          const nextOrder = active && order === "desc" ? "asc" : "desc";
          return (
            <Chip
              key={s.key}
              to={href(basePath, {
                genre,
                sort: s.key === "popular" ? undefined : s.key,
                order: nextOrder === "desc" ? undefined : nextOrder,
              })}
              active={active}
            >
              {s.label}
              {active && <span className="ml-1">{order === "desc" ? "↓" : "↑"}</span>}
            </Chip>
          );
        })}
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        <Chip to={href(basePath, { ...keep, genre: undefined })} active={!genre}>
          전체
        </Chip>
        {shown.map((g) => (
          <Chip key={g} to={href(basePath, { ...keep, genre: g })} active={genre === g}>
            {g}
          </Chip>
        ))}
      </div>
    </div>
  );
}
