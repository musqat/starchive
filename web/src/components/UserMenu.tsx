import Link from "next/link";

import LogOutButton from "@/components/LogOutButton";
import { getMe } from "@/lib/api";

export default async function UserMenu() {
  const user = await getMe();

  if (!user) {
    return (
      <Link href="/login" className="whitespace-nowrap text-[13px] text-muted">
        로그인
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-3 whitespace-nowrap">
      <Link href="/library" className="text-[13px]">
        {user.nickname}
      </Link>
      <LogOutButton />
    </div>
  );
}
