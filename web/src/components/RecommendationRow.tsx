import Link from "next/link";

import Carousel from "@/components/Carousel";
import ContentCard from "@/components/ContentCard";
import { getRecommendations } from "@/lib/api";
import type { ContentType } from "@/lib/types";

export default async function RecommendationRow({
  title,
  type,
}: {
  title: string;
  type: ContentType;
}) {
  const data = await getRecommendations(type);
  if (data.items.length === 0) return null; // 안내는 추천 페이지에 있다

  return (
    <section className="mb-10">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-[15px] font-medium">{title}</h2>
        <Link href="/recommendations" className="text-[13px] text-muted">
          이유 보기
        </Link>
      </div>

      <Carousel>
        {data.items.map((item) => (
          <li key={item.content.id} className="w-32 shrink-0 snap-start sm:w-36">
            <ContentCard item={item.content} />
          </li>
        ))}
      </Carousel>
    </section>
  );
}
