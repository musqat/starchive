import Link from "next/link";

export default function Pagination({
  basePath,
  page,
  lastPage,
  extra = {},
}: {
  basePath: string;
  page: number;
  lastPage: number;
  extra?: Record<string, string>;
}) {
  if (lastPage <= 1) return null;

  const linkTo = (p: number) =>
    `${basePath}?${new URLSearchParams({ ...extra, page: String(p) })}`;

  return (
    <nav className="mt-8 flex items-center justify-center gap-4 text-[13px]">
      {page > 1 ? (
        <Link href={linkTo(page - 1)}>이전</Link>
      ) : (
        <span className="opacity-30">이전</span>
      )}
      <span className="text-muted">
        {page} / {lastPage}
      </span>
      {page < lastPage ? (
        <Link href={linkTo(page + 1)}>다음</Link>
      ) : (
        <span className="opacity-30">다음</span>
      )}
    </nav>
  );
}
