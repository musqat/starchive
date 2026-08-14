"use client";

import { useState } from "react";

import { logIn, signUp } from "@/lib/client";

export default function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(form: FormData) {
    setError(null);
    setPending(true);

    const email = String(form.get("email"));
    const password = String(form.get("password"));

    try {
      if (mode === "signup") {
        await signUp({ email, password, nickname: String(form.get("nickname")) });
      }
      await logIn({ email, password });
      // router.push + refresh 는 경합이 있어 헤더가 갱신되지 않을 때가 있다
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "요청에 실패했습니다");
      setPending(false);
    }
  }

  const field =
    "rounded-lg border border-line bg-fill px-3 py-2.5 text-sm transition " +
    "placeholder:text-muted hover:border-foreground/25 " +
    "focus:border-foreground/50 focus:bg-transparent focus:outline-none";

  return (
    <form action={submit} className="mx-auto flex max-w-sm flex-col gap-2.5 py-12">
      <h1 className="mb-3 text-xl font-medium">{mode === "login" ? "로그인" : "가입"}</h1>

      <input
        name="email"
        type="email"
        required
        placeholder="이메일"
        autoComplete="email"
        className={field}
      />

      {mode === "signup" && (
        <input
          name="nickname"
          required
          maxLength={30}
          placeholder="닉네임"
          className={field}
        />
      )}

      <input
        name="password"
        type="password"
        required
        minLength={8}
        placeholder="비밀번호 (8자 이상)"
        autoComplete={mode === "login" ? "current-password" : "new-password"}
        className={field}
      />

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
        {pending ? "처리 중…" : mode === "login" ? "로그인" : "가입"}
      </button>
    </form>
  );
}
