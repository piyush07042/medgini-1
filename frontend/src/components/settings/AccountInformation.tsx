import Card from "../Card";
import type { User } from "../../types/api";

export default function AccountInformation({ user }: { user: User | null }) {
  return (
    <Card title="Account information">
      <div className="space-y-4">
        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Email</p>
          <p className="mt-2 text-sm font-semibold text-slate-900">{user?.email ?? "Unavailable"}</p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Username</p>
          <p className="mt-2 text-sm font-semibold text-slate-900">{user?.full_name ?? "Unavailable"}</p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Account created</p>
          <p className="mt-2 text-sm font-semibold text-slate-900">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Unavailable"}</p>
        </div>
      </div>
    </Card>
  );
}
