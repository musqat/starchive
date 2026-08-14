import { notFound } from "next/navigation";

import ContentDetailView from "@/components/ContentDetailView";
import Drawer from "@/components/Drawer";
import { getContent } from "@/lib/api";

export default async function ContentDrawer({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const item = await getContent(id).catch(() => null);
  if (!item) notFound();

  return (
    <Drawer pagePath={`/contents/${id}`}>
      <ContentDetailView item={item} />
    </Drawer>
  );
}
