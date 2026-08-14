import Link from "next/link";

import Carousel from "@/components/Carousel";
import ContentCard from "@/components/ContentCard";
import { getContents } from "@/lib/api";
import type { ContentType } from "@/lib/types";

const SIZE = 10;

export default async function ContentRow({
  title,
  href,
  type,
}: {
  title: string;
  href: string;
  type: ContentType;
}) {
  const page = await getContents({ type, size: SIZE });

  return (
    <section className="mb-10">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-[15px] font-medium">{title}</h2>
        <Link href={href} className="text-[13px] text-muted">
          전체 보기
        </Link>
      </div>

      {/* 카드는 서버에서 생성해 children 으로 전달. Carousel 만 클라이언트 */}
      <Carousel>
        {page.items.map((item) => (
          <li key={item.id} className="w-32 shrink-0 snap-start sm:w-36">
            <ContentCard item={item} />
          </li>
        ))}
      </Carousel>
    </section>
  );
}
