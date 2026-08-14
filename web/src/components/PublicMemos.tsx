import MemoText from "@/components/MemoText";
import { getPublicMemos } from "@/lib/api";

/** 남들이 공개로 켠 메모. 없으면 아무것도 그리지 않는다 */
export default async function PublicMemos({ contentId }: { contentId: string }) {
  const memos = await getPublicMemos(contentId).catch(() => []);
  if (memos.length === 0) return null;

  return (
    <section className="mt-6 border-t border-line pt-5">
      <h2 className="mb-3 text-[13px] font-medium">
        다른 사람의 메모 <span className="text-muted">{memos.length}</span>
      </h2>

      <ul className="space-y-4">
        {memos.map((memo) => (
          <li key={`${memo.nickname}-${memo.updated_at}`}>
            <p className="text-[12px] text-muted">
              {memo.nickname}
              {memo.rating && <span className="ml-1.5 text-amber-400">{"★".repeat(memo.rating)}</span>}
            </p>
            <MemoText text={memo.memo} />
          </li>
        ))}
      </ul>
    </section>
  );
}
