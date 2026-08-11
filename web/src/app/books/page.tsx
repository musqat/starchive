import BrowsePage, { type BrowseParams } from "@/components/BrowsePage";

export default async function BooksPage({
  searchParams,
}: {
  searchParams: Promise<BrowseParams>;
}) {
  return (
    <BrowsePage
      type="BOOK"
      basePath="/books"
      label="책"
      unit="권"
      searchParams={await searchParams}
    />
  );
}
