import { redirect } from "next/navigation";

import RecommendationSection from "@/components/RecommendationSection";
import RefreshRecommendations from "@/components/RefreshRecommendations";
import { getMe, getRecommendations } from "@/lib/api";

export const metadata = { title: "추천 · starchive" };

function formatDate(value: string): string {
  const date = new Date(value);
  return `${date.getMonth() + 1}월 ${date.getDate()}일`;
}

export default async function RecommendationsPage() {
  const me = await getMe();
  if (!me) redirect("/login?next=/recommendations");

  const [movie, book] = await Promise.all([
    getRecommendations("MOVIE"),
    getRecommendations("BOOK"),
  ]);

  const made = movie.generated_at ?? book.generated_at;
  const rated = movie.rated_count + book.rated_count;
  const canRefresh = rated >= movie.required_count;
  const hasAny = movie.items.length > 0 || book.items.length > 0;

  return (
    <>
      <div className="mb-1 flex items-baseline justify-between gap-4">
        <h1 className="text-xl font-medium">당신을 위한</h1>
        <div className="flex items-baseline gap-3">
          {made && <span className="text-xs text-muted">{formatDate(made)} 만듦</span>}
          {made && canRefresh && <RefreshRecommendations />}
        </div>
      </div>

      <p className="mb-6 text-xs text-muted">
        {hasAny
          ? `기록한 ${rated}편과 비슷한 취향을 가진 사람들의 평가를 함께 봤어요`
          : "영화나 책을 평가하면 취향에 맞는 작품을 찾아드려요"}
      </p>

      <RecommendationSection
        title="영화"
        type="MOVIE"
        data={movie}
        action={<RefreshRecommendations label="추천 만들기" />}
      />
      <RecommendationSection
        title="책"
        type="BOOK"
        data={book}
        action={<RefreshRecommendations label="추천 만들기" />}
      />
    </>
  );
}
