import type { ContentStatus, ContentType } from "@/lib/types";

/** DB 값은 하나, 문구만 매체에 맞춘다 */
const STATUS: Record<ContentType, Record<ContentStatus, string>> = {
  MOVIE: { WISH: "보고싶어요", DOING: "보는 중", DONE: "봤어요" },
  BOOK: { WISH: "읽고싶어요", DOING: "읽는 중", DONE: "읽었어요" },
  WEBTOON: { WISH: "보고싶어요", DOING: "보는 중", DONE: "봤어요" },
};

export function statusLabel(type: ContentType, status: ContentStatus): string {
  return STATUS[type][status];
}

/** 서재 탭처럼 매체가 섞이는 곳에서 쓴다 */
export const MIXED_STATUS_LABEL: Record<ContentStatus, string> = {
  WISH: "보고싶어요",
  DOING: "보는 중",
  DONE: "봤어요",
};
