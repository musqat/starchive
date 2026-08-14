import Link from "next/link";

import AccountMenu from "@/components/AccountMenu";
import { getMe } from "@/lib/api";

export default async function UserMenu() {
  const user = await getMe();

  if (!user) {
    return (
      <Link
        href="/login"
        className="whitespace-nowrap text-[13px] text-muted transition hover:text-foreground"
      >
        로그인
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-4 whitespace-nowrap">
      <Link href="/library" className="text-sm text-muted transition hover:text-foreground">
        보관함
      </Link>
      <AccountMenu nickname={user.nickname} />
    </div>
  );
}
