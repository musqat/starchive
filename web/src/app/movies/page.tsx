import BrowsePage, { type BrowseParams } from "@/components/BrowsePage";

export default async function MoviesPage({
  searchParams,
}: {
  searchParams: Promise<BrowseParams>;
}) {
  return (
    <BrowsePage
      type="MOVIE"
      basePath="/movies"
      label="영화"
      unit="편"
      searchParams={await searchParams}
    />
  );
}
