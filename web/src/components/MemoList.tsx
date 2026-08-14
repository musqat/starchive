import Image from "next/image";
import Link from "next/link";

import type { LibraryItem } from "@/lib/types";

/** 메모 탭 전용. 포스터만 늘어놓으면 정작 메모가 안 보인다 */
export default function MemoList({ items }: { items: LibraryItem[] }) {
  return (
    <ul className="space-y-4">
      {items.map((item) => (
        <li key={item.content_id}>
          <Link
            href={`/contents/${item.content_id}`}
            className="grid grid-cols-[56px_1fr] gap-4 rounded-lg p-2 transition hover:bg-fill/60"
          >
            <div className="relative aspect-[2/3] overflow-hidden rounded bg-fill">
              {item.content.image_url && (
                <Image
                  src={item.content.image_url}
                  alt=""
                  fill
                  sizes="56px"
                  className="object-cover"
                />
              )}
            </div>

            <div className="min-w-0">
              <p className="flex items-center gap-2 text-[13px]">
                <span className="truncate font-medium">{item.content.title}</span>
                {item.rating && (
                  <span className="shrink-0 text-amber-400">{"★".repeat(item.rating)}</span>
                )}
                {item.memo_public && (
                  <span className="shrink-0 rounded-full bg-fill px-1.5 py-0.5 text-[10px] text-muted">
                    공개
                  </span>
                )}
              </p>
              {/* 목록이라 2줄까지. 전체는 눌러 들어가서 본다 */}
              <p className="mt-1 line-clamp-2 text-sm leading-6 whitespace-pre-wrap text-muted">
                {item.memo}
              </p>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
