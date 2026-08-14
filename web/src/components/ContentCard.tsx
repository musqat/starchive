import Image from "next/image";
import Link from "next/link";

import StatusToggle from "@/components/StatusToggle";
import type { ContentSummary } from "@/lib/types";

export default function ContentCard({ item }: { item: ContentSummary }) {
  return (
    <div className="group relative">
      <StatusToggle item={item} />
      <Link href={`/contents/${item.id}`} className="block">
        <div className="relative aspect-[2/3] overflow-hidden rounded-lg bg-fill">
          {item.image_url ? (
            <Image
              src={item.image_url}
              alt=""
              fill
              sizes="(max-width: 640px) 33vw, 20vw"
              className="object-cover transition-transform group-hover:scale-105"
            />
          ) : (
            <div className="grid h-full place-items-center text-xs text-muted">
              이미지 없음
            </div>
          )}
        </div>
        <p className="mt-2 line-clamp-2 text-[13px] leading-snug">{item.title}</p>
        <p className="line-clamp-1 text-xs text-muted">{item.creator ?? " "}</p>
        <p className="text-xs text-muted">
          {/* 알라딘은 리뷰가 없으면 0. 0.0 으로 표시하면 실제 평점처럼 읽힘 */}
          {item.external_rating ? `★ ${item.external_rating.toFixed(1)}` : "평가 없음"}
        </p>
      </Link>
    </div>
  );
}
