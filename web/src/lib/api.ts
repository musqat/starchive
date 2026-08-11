const BASE = process.env.NEXT_PUBLIC_API_URL;

export type ContentType = "MOVIE" | "BOOK" | "WEBTOON";

export type ContentSummary = {
  id: string;
  type: ContentType;
  title: string;
  creator: string | null;
  genre: string[] | null;
  image_url: string | null;
  external_rating: number | null;
};

export type ContentDetail = ContentSummary & {
  description: string | null;
  release_date: string | null;
  external_popularity: number | null;
  content_metadata: Record<string, unknown>;
};

export type ContentPage = {
  items: ContentSummary[];
  total: number;
  page: number;
  size: number;
};

export type SortKey = "popular" | "rating" | "recent";
export type SortOrder = "desc" | "asc";

type ListParams = {
  type?: ContentType;
  q?: string;
  genre?: string;
  sort?: SortKey;
  order?: SortOrder;
  page?: number;
  size?: number;
};

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${res.status} ${path}`);
  }
  return res.json();
}

export function getContents(params: ListParams = {}): Promise<ContentPage> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  }
  const qs = query.toString();
  return get<ContentPage>(`/contents${qs ? `?${qs}` : ""}`);
}

export function getContent(id: string): Promise<ContentDetail> {
  return get<ContentDetail>(`/contents/${encodeURIComponent(id)}`);
}

export function getGenres(type: ContentType): Promise<string[]> {
  return get<string[]>(`/contents/genres?type=${type}`);
}
