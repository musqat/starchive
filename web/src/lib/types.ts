export type ContentType = "MOVIE" | "BOOK" | "WEBTOON";

export type ContentSummary = {
  id: string;
  type: ContentType;
  title: string;
  creator: string | null;
  genre: string[] | null;
  image_url: string | null;
  external_rating: number | null;

  // 로그인했을 때만 채워진다
  my_status: ContentStatus | null;
  my_rating: number | null;
  my_recommended: boolean;
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

export type ContentStatus = "WISH" | "DOING" | "DONE";

export type User = {
  id: number;
  email: string;
  nickname: string;
  created_at: string;
};

export type ContentRecord = {
  content_id: string;
  status: ContentStatus;
  rating: number | null;
  recommended: boolean;
  updated_at: string;
};

export type LibraryItem = ContentRecord & {
  content: ContentSummary;
};
