"use client";

import type { ContentRecord, ContentStatus, User } from "@/lib/types";

/** next.config 의 rewrite 로 백엔드에 닿는다. 같은 출처라 쿠키가 이 도메인에 저장된다 */
const BASE = "/api";

/** 브라우저에서 부르는 쪽. credentials 로 쿠키를 주고받는다 */
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: { "content-type": "application/json", ...init.headers },
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `${res.status}`);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export function signUp(body: { email: string; password: string; nickname: string }) {
  return request<User>("/auth/signup", { method: "POST", body: JSON.stringify(body) });
}

export function logIn(body: { email: string; password: string }) {
  return request<User>("/auth/login", { method: "POST", body: JSON.stringify(body) });
}

export function logOut() {
  return request<void>("/auth/logout", { method: "POST" });
}

export function changePassword(body: { current_password: string; new_password: string }) {
  return request<void>("/auth/password", { method: "PATCH", body: JSON.stringify(body) });
}

export function withdraw(body: { password: string }) {
  return request<void>("/auth/withdraw", { method: "POST", body: JSON.stringify(body) });
}

export function putRecord(
  contentId: string,
  body: {
    status?: ContentStatus;
    rating?: number | null;
    liked?: boolean;
    recommended?: boolean;
    memo?: string | null;
    memo_public?: boolean;
  },
) {
  return request<ContentRecord>(`/me/records/${encodeURIComponent(contentId)}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function deleteRecord(contentId: string) {
  return request<void>(`/me/records/${encodeURIComponent(contentId)}`, { method: "DELETE" });
}
