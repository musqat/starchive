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
  my_liked: boolean;
  my_recommended: boolean;
};

export type ContentDetail = ContentSummary & {
  description: string | null;
  release_date: string | null;
  external_popularity: number | null;
  content_metadata: Record<string, unknown>;

  // 메모는 상세에만 실린다
  my_memo: string | null;
  my_memo_public: boolean;
};

export type PublicMemo = {
  nickname: string;
  memo: string;
  rating: number | null;
  updated_at: string;
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
  liked: boolean;
  recommended: boolean;
  memo: string | null;
  memo_public: boolean;
  updated_at: string;
};

export type LibraryItem = ContentRecord & {
  content: ContentSummary;
};

export type ReasonSource = "LLM" | "TEMPLATE" | "RECENT";

export type RecommendationItem = {
  rank: number;
  reason: string | null;
  /** TEMPLATE 은 전 사용자에게 같은 문장이라 화면에 쓰지 않는다 */
  reason_source: ReasonSource;
  content: ContentSummary;
};

export type RecommendationList = {
  items: RecommendationItem[];
  generated_at: string | null;
  rated_count: number;
  required_count: number;
};

export type RefreshResult = {
  movie: RecommendationList;
  book: RecommendationList;
};
