import Link from "next/link";

import AuthForm from "@/components/AuthForm";

export default function SignUpPage() {
  return (
    <>
      <AuthForm mode="signup" />
      <p className="text-center text-[13px] text-muted">
        이미 계정이 있나요?{" "}
        <Link href="/login" className="text-foreground underline">
          로그인
        </Link>
      </p>
    </>
  );
}
