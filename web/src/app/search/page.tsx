import Link from "next/link";

import ContentGrid from "@/components/ContentGrid";
import Pagination from "@/components/Pagination";
import { getContents, type ContentType } from "@/lib/api";

const SIZE = 20;

const CHIPS: { label: string; type?: "MOVIE" | "BOOK" }[] = [
  { label: "전체" },
  { label: "영화", type: "MOVIE" },
  { label: "책", type: "BOOK" },
];

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; type?: ContentType; page?: string }>;
}) {
  const { q = "", type, page: rawPage } = await searchParams;
  const page = Number(rawPage ?? 1);

  if (!q) {
    return <p className="py-16 text-center text-sm text-muted">검색어를 입력하세요</p>;
  }

  // 칩에 붙일 건수. size=1 로 total 만 사용 (size=0 은 API 가 거절)
  const [movies, books] = await Promise.all([
    getContents({ type: "MOVIE", q, size: 1 }),
    getContents({ type: "BOOK", q, size: 1 }),
  ]);
  const counts = { MOVIE: movies.total, BOOK: books.total };
  const total = counts.MOVIE + counts.BOOK;

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {CHIPS.map((chip) => {
          const active = chip.type === type;
          const n = chip.type ? counts[chip.type] : total;
          return (
            <Link
              key={chip.label}
              href={`/search?${new URLSearchParams({ q, ...(chip.type ? { type: chip.type } : {}) })}`}
              className={`rounded-full px-3 py-1 text-[13px] ${
                active ? "bg-foreground text-background" : "bg-fill text-muted"
              }`}
            >
              {chip.label} {n.toLocaleString()}
            </Link>
          );
        })}
      </div>

      {total === 0 ? (
        <p className="py-16 text-center text-sm text-muted">
          &ldquo;{q}&rdquo; 검색 결과가 없습니다
        </p>
      ) : type ? (
        <SingleType q={q} type={type} page={page} />
      ) : (
        <>
          {counts.MOVIE > 0 && <Group q={q} type="MOVIE" label="영화" total={counts.MOVIE} />}
          {counts.BOOK > 0 && <Group q={q} type="BOOK" label="책" total={counts.BOOK} />}
        </>
      )}
    </>
  );
}

async function SingleType({
  q,
  type,
  page,
}: {
  q: string;
  type: ContentType;
  page: number;
}) {
  const data = await getContents({ type, q, page, size: SIZE });

  return (
    <>
      <ContentGrid items={data.items} />
      <Pagination
        basePath="/search"
        page={page}
        lastPage={Math.ceil(data.total / SIZE)}
        extra={{ q, type }}
      />
    </>
  );
}

async function Group({
  q,
  type,
  label,
  total,
}: {
  q: string;
  type: ContentType;
  label: string;
  total: number;
}) {
  const data = await getContents({ type, q, size: 4 });
  const more = total > data.items.length;

  return (
    <section className="mb-8">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-[15px] font-medium">
          {label} <span className="text-muted">{total.toLocaleString()}</span>
        </h2>
        {more && (
          <Link
            href={`/search?${new URLSearchParams({ q, type })}`}
            className="text-[13px] text-muted"
          >
            더 보기
          </Link>
        )}
      </div>
      <ContentGrid items={data.items} />
    </section>
  );
}
