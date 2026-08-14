import ContentGrid from "@/components/ContentGrid";
import Filters from "@/components/Filters";
import Pagination from "@/components/Pagination";
import { getContents, getGenres } from "@/lib/api";
import type { ContentType, SortKey, SortOrder } from "@/lib/types";

const SIZE = 20;

export type BrowseParams = {
  genre?: string;
  sort?: SortKey;
  order?: SortOrder;
  page?: string;
};

export default async function BrowsePage({
  type,
  basePath,
  label,
  unit,
  searchParams,
}: {
  type: ContentType;
  basePath: string;
  label: string;
  unit: string;
  searchParams: BrowseParams;
}) {
  const { genre, sort = "popular", order = "desc" } = searchParams;
  const page = Number(searchParams.page ?? 1);

  const [data, genres] = await Promise.all([
    getContents({ type, genre, sort, order, page, size: SIZE }),
    getGenres(type),
  ]);

  return (
    <>
      <div className="mb-4 flex items-baseline justify-between">
        <h1 className="text-[15px] font-medium">{label}</h1>
        <span className="text-[13px] text-muted">
          {data.total.toLocaleString()}
          {unit}
        </span>
      </div>

      <Filters
        basePath={basePath}
        genres={genres}
        genre={genre}
        sort={sort}
        order={order}
      />

      {data.items.length === 0 ? (
        <p className="py-16 text-center text-sm text-muted">해당하는 항목이 없습니다</p>
      ) : (
        <ContentGrid items={data.items} />
      )}

      <Pagination
        basePath={basePath}
        page={page}
        lastPage={Math.ceil(data.total / SIZE)}
        extra={{
          ...(genre ? { genre } : {}),
          ...(sort !== "popular" ? { sort } : {}),
          ...(order !== "desc" ? { order } : {}),
        }}
      />
    </>
  );
}
