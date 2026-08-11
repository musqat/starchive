import { notFound } from "next/navigation";

import ContentDetailView from "@/components/ContentDetailView";
import { getContent } from "@/lib/api";

export default async function ContentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const item = await getContent(id).catch(() => null);
  if (!item) notFound();

  return <ContentDetailView item={item} />;
}
