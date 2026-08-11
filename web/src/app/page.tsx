import ContentRow from "@/components/ContentRow";

export default function HomePage() {
  return (
    <>
      <ContentRow title="인기 영화" href="/movies" type="MOVIE" />
      <ContentRow title="인기 책" href="/books" type="BOOK" />
    </>
  );
}
