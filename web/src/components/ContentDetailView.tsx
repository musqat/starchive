import Image from "next/image";

import type { ContentDetail } from "@/lib/types";

export default function ContentDetailView({ item }: { item: ContentDetail }) {
  return (
    <article className="grid gap-6 sm:grid-cols-[180px_1fr]">
      <div className="relative aspect-[2/3] w-full max-w-[180px] overflow-hidden rounded-lg bg-fill">
        {item.image_url && (
          <Image src={item.image_url} alt="" fill sizes="180px" className="object-cover" />
        )}
      </div>

      <div>
        <h1 className="text-xl font-medium">{item.title}</h1>
        <p className="mt-1 text-[13px] text-muted">
          {[item.creator, item.release_date].filter(Boolean).join(" · ")}
        </p>

        {item.genre && item.genre.length > 0 && (
          <ul className="mt-3 flex flex-wrap gap-1.5">
            {item.genre.map((g) => (
              <li key={g} className="rounded-full bg-fill px-2.5 py-0.5 text-xs">
                {g}
              </li>
            ))}
          </ul>
        )}

        <p className="mt-3 text-sm">
          {/* 알라딘은 리뷰가 없으면 0. 0.0 으로 표시하면 실제 평점처럼 읽힘 */}
          {item.external_rating ? `★ ${item.external_rating.toFixed(1)}` : "평가 없음"}
          {item.external_popularity != null && (
            <span className="ml-1 text-[13px] text-muted">
              · {item.external_popularity.toLocaleString()}
            </span>
          )}
        </p>

        {item.description && (
          <p className="mt-4 text-sm leading-7 text-muted">{item.description}</p>
        )}
      </div>
    </article>
  );
}
