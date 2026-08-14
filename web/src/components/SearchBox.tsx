import type { ContentType } from "@/lib/types";

const SCOPES: { value: string; label: string }[] = [
  { value: "", label: "통합" },
  { value: "MOVIE", label: "영화" },
  { value: "BOOK", label: "책" },
];

export default function SearchBox({
  defaultQuery = "",
  defaultType,
}: {
  defaultQuery?: string;
  defaultType?: ContentType;
}) {
  return (
    <form
      action="/search"
      className="flex w-full items-stretch overflow-hidden rounded-full border border-line bg-fill"
    >
      {/* native select 라 JS 없이 제출. SearchBox 는 서버 컴포넌트 유지 */}
      <select
        name="type"
        defaultValue={defaultType ?? ""}
        aria-label="검색 범위"
        className="appearance-none bg-transparent py-2 pl-4 pr-6 text-sm text-muted focus:outline-none"
      >
        {SCOPES.map((s) => (
          <option key={s.value} value={s.value} className="bg-background">
            {s.label}
          </option>
        ))}
      </select>

      <span aria-hidden className="self-center text-xs text-muted">
        ▾
      </span>

      <input
        name="q"
        defaultValue={defaultQuery}
        placeholder="제목 검색"
        aria-label="제목 검색"
        className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm placeholder:text-muted focus:outline-none"
      />

      {/* select 가 있으면 입력 필드 하나짜리 폼의 Enter 암묵 제출이 안 걸림 */}
      <button type="submit" aria-label="검색" className="px-4 text-sm text-muted">
        ⌕
      </button>
    </form>
  );
}
