import Link from "next/link";
import { redirect } from "next/navigation";

import ContentGrid from "@/components/ContentGrid";
import MemoList from "@/components/MemoList";
import { getLibrary } from "@/lib/api";

/** 화면에서 만들 수 있는 신호만 탭으로 둔다 */
const TABS = [
  { key: "", label: "전체" },
  { key: "liked", label: "좋아요" },
  { key: "recommended", label: "추천해요" },
  { key: "memo", label: "댓글" },
] as const;

type Filter = (typeof TABS)[number]["key"];

export default async function LibraryPage({
  searchParams,
}: {
  searchParams: Promise<{ filter?: Filter }>;
}) {
  const { filter = "" } = await searchParams;

  const items = await getLibrary({
    liked: filter === "liked" ? true : undefined,
    recommended: filter === "recommended" ? true : undefined,
    has_memo: filter === "memo" ? true : undefined,
    size: 100,
  }).catch(() => null);
  if (!items) redirect("/login");

  return (
    <>
      <h1 className="mb-4 text-[15px] font-medium">보관함</h1>

      <div className="mb-5 flex flex-wrap gap-2">
        {TABS.map((tab) => (
          <Link
            key={tab.label}
            href={tab.key ? `/library?filter=${tab.key}` : "/library"}
            className={`rounded-full px-3 py-1 text-[13px] ${
              filter === tab.key ? "bg-foreground text-background" : "bg-fill text-muted"
            }`}
          >
            {tab.label}
          </Link>
        ))}
      </div>

      {items.length === 0 ? (
        <p className="py-16 text-center text-sm text-muted">
          아직 기록이 없습니다.{" "}
          <Link href="/movies" className="text-foreground underline">
            둘러보기
          </Link>
        </p>
      ) : filter === "memo" ? (
        <MemoList items={items} />
      ) : (
        <ContentGrid items={items.map((item) => item.content)} />
      )}
    </>
  );
}
