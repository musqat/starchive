import Image from "next/image";
import Link from "next/link";

import RecommendationEmpty from "@/components/RecommendationEmpty";
import type { ContentType, RecommendationItem, RecommendationList } from "@/lib/types";

export default function RecommendationSection({
  title,
  type,
  data,
  action,
}: {
  title: string;
  type: ContentType;
  data: RecommendationList;
  action?: React.ReactNode;
}) {
  return (
    <section className="mb-8">
      <div className="mb-2 flex items-baseline gap-2">
        <h2 className="text-[15px] font-medium">{title}</h2>
        {data.items.length > 0 && (
          <span className="text-xs text-muted">{data.items.length}편</span>
        )}
      </div>

      {data.items.length === 0 ? (
        <RecommendationEmpty
          type={type}
          rated={data.rated_count}
          required={data.required_count}
          requiredRating={data.required_rating}
          action={action}
        />
      ) : (
        <ul className="grid grid-cols-1 gap-x-6 sm:grid-cols-2">
          {data.items.map((item) => (
            <Row key={item.content.id} item={item} />
          ))}
        </ul>
      )}
    </section>
  );
}

function Row({ item }: { item: RecommendationItem }) {
  const { content } = item;
  // 템플릿은 LLM 실패 시 붙는 같은 문장이라 반복된다. 신작 자리 안내는 보여준다
  const reason = item.reason_source === "TEMPLATE" ? null : item.reason;

  return (
    <li className="border-t border-line">
      <Link href={`/contents/${content.id}`} className="flex gap-2.5 py-2.5">
        <span className="w-4 shrink-0 pt-0.5 text-xs text-muted">{item.rank}</span>

        <div className="relative aspect-[2/3] w-[38px] shrink-0 overflow-hidden rounded-md bg-fill">
          {content.image_url && (
            <Image src={content.image_url} alt="" fill sizes="76px" className="object-cover" />
          )}
        </div>

        <div className="min-w-0">
          <p className="line-clamp-1 text-[13px]">{content.title}</p>
          <p className="line-clamp-1 text-[11px] text-muted">{content.creator ?? " "}</p>
          {reason && (
            <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-foreground/75">
              {reason}
            </p>
          )}
        </div>
      </Link>
    </li>
  );
}
