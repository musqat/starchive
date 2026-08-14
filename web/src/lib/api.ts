import { cookies } from "next/headers";

import type {
  ContentDetail,
  ContentPage,
  ContentStatus,
  ContentType,
  LibraryItem,
  PublicMemo,
  SortKey,
  SortOrder,
  User,
} from "@/lib/types";

/** 서버는 rewrite 를 거칠 필요가 없어 백엔드로 바로 간다 */
const BASE = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

type ListParams = {
  type?: ContentType;
  q?: string;
  genre?: string;
  sort?: SortKey;
  order?: SortOrder;
  unseen?: boolean;
  page?: number;
  size?: number;
};

function toQuery(params: Record<string, unknown>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

/** 서버 컴포넌트는 브라우저 쿠키를 자동으로 넘기지 않아 직접 실어야 한다 */
async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    cache: "no-store",
    headers: { cookie: (await cookies()).toString() },
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${path}`);
  }
  return res.json();
}

export function getContents(params: ListParams = {}): Promise<ContentPage> {
  return get<ContentPage>(`/contents${toQuery(params)}`);
}

export function getContent(id: string): Promise<ContentDetail> {
  return get<ContentDetail>(`/contents/${encodeURIComponent(id)}`);
}

export function getPublicMemos(id: string): Promise<PublicMemo[]> {
  return get<PublicMemo[]>(`/contents/${encodeURIComponent(id)}/memos`);
}

export function getGenres(type: ContentType): Promise<string[]> {
  return get<string[]>(`/contents/genres?type=${type}`);
}

/** 비로그인이면 null */
export function getMe(): Promise<User | null> {
  return get<User>("/auth/me").catch(() => null);
}

export function getLibrary(
  params: {
    status?: ContentStatus;
    type?: ContentType;
    liked?: boolean;
    recommended?: boolean;
    has_memo?: boolean;
    page?: number;
    size?: number;
  } = {},
): Promise<LibraryItem[]> {
  return get<LibraryItem[]>(`/me/library${toQuery(params)}`);
}
