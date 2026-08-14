import Link from "next/link";

import AuthForm from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <>
      <AuthForm mode="login" />
      <p className="text-center text-[13px] text-muted">
        계정이 없나요?{" "}
        <Link href="/signup" className="text-foreground underline">
          가입
        </Link>
      </p>
    </>
  );
}
