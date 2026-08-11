import ContentCard from "@/components/ContentCard";
import type { ContentSummary } from "@/lib/api";

export default function ContentGrid({ items }: { items: ContentSummary[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {items.map((item) => (
        <ContentCard key={item.id} item={item} />
      ))}
    </div>
  );
}
