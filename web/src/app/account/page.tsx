import { redirect } from "next/navigation";

import { PasswordForm, WithdrawForm } from "@/components/AccountForms";
import { getMe } from "@/lib/api";

export default async function AccountPage() {
  const me = await getMe();
  if (!me) redirect("/login");

  return (
    <div className="mx-auto max-w-sm space-y-8 py-12">
      <div>
        <h1 className="text-xl font-medium">{me.nickname}</h1>
        <p className="mt-1 text-[13px] text-muted">{me.email}</p>
      </div>

      <PasswordForm />

      <div className="border-t border-line pt-8">
        <WithdrawForm />
      </div>
    </div>
  );
}
