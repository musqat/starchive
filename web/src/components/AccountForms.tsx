"use client";

import { useState } from "react";

import { changePassword, withdraw } from "@/lib/client";

const field =
  "rounded-lg border border-line bg-fill px-3 py-2.5 text-sm transition " +
  "placeholder:text-muted hover:border-foreground/25 " +
  "focus:border-foreground/50 focus:bg-transparent focus:outline-none";

export function PasswordForm() {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(form: FormData) {
    setMessage(null);
    setError(null);
    setPending(true);

    try {
      await changePassword({
        current_password: String(form.get("current")),
        new_password: String(form.get("next")),
      });
      setMessage("비밀번호를 바꿨습니다");
    } catch (e) {
      setError(e instanceof Error ? e.message : "요청에 실패했습니다");
    }
    setPending(false);
  }

  return (
    <form action={submit} className="flex flex-col gap-2.5">
      <h2 className="text-[15px] font-medium">비밀번호 변경</h2>

      <input
        name="current"
        type="password"
        required
        placeholder="현재 비밀번호"
        autoComplete="current-password"
        className={field}
      />
      <input
        name="next"
        type="password"
        required
        minLength={8}
        placeholder="새 비밀번호 (8자 이상)"
        autoComplete="new-password"
        className={field}
      />

      {message && <p className="text-[13px] text-muted">{message}</p>}
      {error && (
        <p role="alert" className="rounded-lg bg-red-500/10 px-3 py-2 text-[13px] text-red-400">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="mt-1 rounded-lg bg-foreground px-3 py-2.5 text-sm font-medium text-background transition
                   hover:bg-foreground/85 active:scale-[0.99]
                   disabled:cursor-not-allowed disabled:opacity-40"
      >
        {pending ? "처리 중…" : "변경"}
      </button>
    </form>
  );
}

export function WithdrawForm() {
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(form: FormData) {
    setError(null);
    setPending(true);

    try {
      await withdraw({ password: String(form.get("password")) });
      // 서버 컴포넌트가 쿠키를 다시 읽도록 전체 새로고침
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "요청에 실패했습니다");
      setPending(false);
    }
  }

  if (!confirming) {
    return (
      <div>
        <h2 className="text-[15px] font-medium">회원 탈퇴</h2>
        <p className="mt-1 text-[13px] text-muted">
          계정과 기록이 모두 지워집니다. 되돌릴 수 없습니다
        </p>
        <button
          type="button"
          onClick={() => setConfirming(true)}
          className="mt-3 rounded-lg border border-red-500/40 px-3 py-2 text-[13px] text-red-400 transition hover:bg-red-500/10"
        >
          탈퇴하기
        </button>
      </div>
    );
  }

  return (
    <form action={submit} className="flex flex-col gap-2.5">
      <h2 className="text-[15px] font-medium">회원 탈퇴</h2>
      <p className="text-[13px] text-muted">확인을 위해 비밀번호를 입력하세요</p>

      <input
        name="password"
        type="password"
        required
        placeholder="비밀번호"
        autoComplete="current-password"
        className={field}
      />

      {error && (
        <p role="alert" className="rounded-lg bg-red-500/10 px-3 py-2 text-[13px] text-red-400">
          {error}
        </p>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={pending}
          className="rounded-lg bg-red-500 px-3 py-2.5 text-sm font-medium text-white transition
                     hover:bg-red-500/85 active:scale-[0.99]
                     disabled:cursor-not-allowed disabled:opacity-40"
        >
          {pending ? "처리 중…" : "탈퇴"}
        </button>
        <button
          type="button"
          onClick={() => setConfirming(false)}
          className="rounded-lg bg-fill px-3 py-2.5 text-sm text-muted transition hover:text-foreground"
        >
          취소
        </button>
      </div>
    </form>
  );
}
