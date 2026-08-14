"use client";

import { logOut } from "@/lib/client";

export default function LogOutButton() {
  async function handle() {
    await logOut();
    // 서버 컴포넌트가 쿠키를 다시 읽도록 전체 새로고침
    window.location.assign("/");
  }

  return (
    <button type="button" onClick={handle} className="text-[13px] text-muted">
      로그아웃
    </button>
  );
}
