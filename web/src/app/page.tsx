import ContentRow from "@/components/ContentRow";
import RecommendationRow from "@/components/RecommendationRow";
import { getMe } from "@/lib/api";

export default async function HomePage() {
  const me = await getMe();

  return (
    <>
      {/* 비로그인이면 아예 안 그린다*/}
      {me && (
        <>
          <RecommendationRow title="당신을 위한 영화" type="MOVIE" />
          <RecommendationRow title="당신을 위한 책" type="BOOK" />
        </>
      )}
      <ContentRow title="인기 영화" href="/movies" type="MOVIE" />
      <ContentRow title="인기 책" href="/books" type="BOOK" />
    </>
  );
}
