import Image from "next/image";

import DetailActions from "@/components/DetailActions";
import MemoForm from "@/components/MemoForm";
import PublicMemos from "@/components/PublicMemos";
import WatchLinks from "@/components/WatchLinks";
import type { ContentDetail } from "@/lib/types";

/** 매체별로 다른 필드. 없으면 그 줄이 그려지지 않는다 */
type Meta = {
  runtime?: number;
  cast?: string[];
  original_title?: string;
  publisher?: string;
  author?: string;
};

export default function ContentDetailView({ item }: { item: ContentDetail }) {
  const meta = item.content_metadata as Meta;
  const isMovie = item.type === "MOVIE";

  const subtitle = [
    item.creator,
    item.release_date,
    meta.runtime ? `${meta.runtime}분` : null,
  ].filter(Boolean);

  const people = isMovie ? meta.cast?.join(", ") : meta.author;

  return (
    // 전체 페이지에서는 가운데로 모은다. 드로어(max-w-xl) 안에서는 그대로 꽉 찬다
    <article className="mx-auto grid max-w-3xl gap-6 sm:grid-cols-[200px_minmax(0,1fr)] sm:gap-8">
      <div>
        <div className="relative aspect-[2/3] w-full max-w-[200px] overflow-hidden rounded-lg bg-fill">
          {item.image_url && (
            <Image src={item.image_url} alt="" fill sizes="200px" className="object-cover" />
          )}
        </div>
        {/* 좋아요·추천해요가 조건부로 생기므로 고정된 것을 위에 둔다 */}
        <WatchLinks item={item} />
        <DetailActions item={item} />
      </div>

      <div>
        <h1 className="text-2xl font-medium">{item.title}</h1>

        {subtitle.length > 0 && (
          <p className="mt-1 text-[13px] text-muted">{subtitle.join(" · ")}</p>
        )}

        {isMovie && meta.original_title && (
          <p className="text-xs text-muted/70">{meta.original_title}</p>
        )}
        {!isMovie && meta.publisher && (
          <p className="text-xs text-muted/70">{meta.publisher}</p>
        )}

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

        {people && (
          <div className="mt-4 border-t border-line pt-3">
            <p className="text-[11px] text-muted">{isMovie ? "출연" : "참여"}</p>
            <p className="mt-0.5 text-[13px]">{people}</p>
          </div>
        )}

        {item.description && (
          <p className="mt-4 text-sm leading-7 text-muted">{item.description}</p>
        )}

        <MemoForm item={item} />
        <PublicMemos contentId={item.id} />
      </div>
    </article>
  );
}
