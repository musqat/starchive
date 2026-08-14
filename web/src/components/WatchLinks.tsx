import Image from "next/image";

import type { ContentDetail } from "@/lib/types";

const TMDB_LOGO = "https://image.tmdb.org/t/p/w92";
const ALADIN_PRODUCT = "https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=";

type Provider = { name: string; logo_path: string | null; kind: string };
type Providers = { link: string | null; items: Provider[] };

type Meta = {
  providers?: Providers | null;
  itemId?: number;
};

/** 영화는 TMDB(JustWatch), 책은 알라딘 상품 페이지 */
export default function WatchLinks({ item }: { item: ContentDetail }) {
  const meta = item.content_metadata as Meta;

  if (item.type === "BOOK") {
    if (!meta.itemId) return null;
    return (
      <Section title="구매">
        <a
          href={`${ALADIN_PRODUCT}${meta.itemId}`}
          target="_blank"
          rel="noreferrer noopener"
          className="block rounded-lg bg-fill px-3 py-2.5 text-center text-[13px] transition hover:bg-fill/70"
        >
          알라딘에서 보기 →
        </a>
      </Section>
    );
  }

  const providers = meta.providers;
  if (!providers?.items?.length) return null;

  return (
    <Section title="볼 수 있는 곳">
      <div className="flex flex-wrap gap-2">
        {providers.items.map((provider) => (
          <span key={provider.name} title={provider.name} className="relative h-11 w-11">
            {provider.logo_path ? (
              <Image
                src={`${TMDB_LOGO}${provider.logo_path}`}
                alt={provider.name}
                fill
                sizes="44px"
                className="rounded-xl object-cover"
              />
            ) : (
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-fill text-[11px]">
                {provider.name.slice(0, 2)}
              </span>
            )}
          </span>
        ))}
      </div>

      {/* JustWatch 자료라 개별 서비스로 바로 보내지 않고 TMDB 가 준 링크로 보낸다 */}
      {providers.link && (
        <a
          href={providers.link}
          target="_blank"
          rel="noreferrer noopener"
          className="mt-2 block text-[11px] text-muted underline"
        >
          보러 가기
        </a>
      )}
    </Section>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-4">
      <p className="mb-1.5 text-[11px] text-muted">{title}</p>
      {children}
    </div>
  );
}
