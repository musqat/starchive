import Link from "next/link";
import { redirect } from "next/navigation";

import ContentGrid from "@/components/ContentGrid";
import { getLibrary } from "@/lib/api";
import { MIXED_STATUS_LABEL } from "@/lib/labels";
import type { ContentStatus } from "@/lib/types";

const TABS: { label: string; status?: ContentStatus }[] = [
  { label: "전체" },
  { label: MIXED_STATUS_LABEL.WISH, status: "WISH" },
  { label: MIXED_STATUS_LABEL.DOING, status: "DOING" },
  { label: MIXED_STATUS_LABEL.DONE, status: "DONE" },
];

export default async function LibraryPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: ContentStatus }>;
}) {
  const { status } = await searchParams;

  const items = await getLibrary({ status, size: 100 }).catch(() => null);
  if (!items) redirect("/login");

  return (
    <>
      <h1 className="mb-4 text-[15px] font-medium">보관함</h1>

      <div className="mb-5 flex flex-wrap gap-2">
        {TABS.map((tab) => (
          <Link
            key={tab.label}
            href={tab.status ? `/library?status=${tab.status}` : "/library"}
            className={`rounded-full px-3 py-1 text-[13px] ${
              status === tab.status ? "bg-foreground text-background" : "bg-fill text-muted"
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
      ) : (
        <ContentGrid items={items.map((item) => item.content)} />
      )}
    </>
  );
}
