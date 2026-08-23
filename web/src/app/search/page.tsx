import Link from "next/link";

import ContentGrid from "@/components/ContentGrid";
import { searchContents } from "@/lib/api";
import type { ContentSummary, ContentType } from "@/lib/types";

const PREVIEW = 4; // 전체 뷰에서 매체별 미리보기 개수

const CHIPS: { label: string; type?: "MOVIE" | "BOOK" }[] = [
  { label: "전체" },
  { label: "영화", type: "MOVIE" },
  { label: "책", type: "BOOK" },
];

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; type?: ContentType }>;
}) {
  const { q = "", type } = await searchParams;

  if (!q) {
    return <p className="py-16 text-center text-sm text-muted">검색어를 입력하세요</p>;
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
        <Chips q={q} active={type} />
        <QueryLabel q={q} />
      </div>
      {type ? <Single q={q} type={type} /> : <Both q={q} />}
    </>
  );
}

function QueryLabel({ q }: { q: string }) {
  const shown = q.length > 20 ? `${q.slice(0, 20)}…` : q;
  return (
    <p className="shrink-0 text-[13px] text-muted">
      <span className="text-foreground">&ldquo;{shown}&rdquo;</span> 검색 결과
    </p>
  );
}

function Chips({ q, active }: { q: string; active?: ContentType }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {CHIPS.map((chip) => (
        <Link
          key={chip.label}
          href={`/search?${new URLSearchParams({ q, ...(chip.type ? { type: chip.type } : {}) })}`}
          className={`rounded-full px-3 py-1 text-[13px] ${
            chip.type === active ? "bg-foreground text-background" : "bg-fill text-muted"
          }`}
        >
          {chip.label}
        </Link>
      ))}
    </div>
  );
}

function Empty({ q }: { q: string }) {
  return (
    <p className="py-16 text-center text-sm text-muted">
      &ldquo;{q}&rdquo; 검색 결과가 없습니다
    </p>
  );
}

// 자연어 질의일 때 LLM 이 결과를 보고 쓴 한 줄
function Comment({ text }: { text: string }) {
  return (
    <p className="mb-5 rounded-lg bg-fill px-4 py-3 text-sm leading-relaxed">
      <span className="mr-1">✨</span>
      {text}
    </p>
  );
}

async function Single({ q, type }: { q: string; type: ContentType }) {
  const { comment, items } = await searchContents(q, type);
  if (items.length === 0) return <Empty q={q} />;
  return (
    <>
      {comment && <Comment text={comment} />}
      <ContentGrid items={items} />
    </>
  );
}

async function Both({ q }: { q: string }) {
  const [movies, books] = await Promise.all([
    searchContents(q, "MOVIE"),
    searchContents(q, "BOOK"),
  ]);

  if (movies.items.length + books.items.length === 0) {
    return <Empty q={q} />;
  }

  const comment = movies.comment ?? books.comment;

  return (
    <>
      {comment && <Comment text={comment} />}
      {movies.items.length > 0 && <Group q={q} type="MOVIE" label="영화" items={movies.items} />}
      {books.items.length > 0 && <Group q={q} type="BOOK" label="책" items={books.items} />}
    </>
  );
}

function Group({
  q,
  type,
  label,
  items,
}: {
  q: string;
  type: ContentType;
  label: string;
  items: ContentSummary[];
}) {
  return (
    <section className="mb-8">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-[15px] font-medium">{label}</h2>
        {items.length > PREVIEW && (
          <Link
            href={`/search?${new URLSearchParams({ q, type })}`}
            className="text-[13px] text-muted"
          >
            더 보기
          </Link>
        )}
      </div>
      <ContentGrid items={items.slice(0, PREVIEW)} />
    </section>
  );
}
