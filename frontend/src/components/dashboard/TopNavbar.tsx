import { Bell, Search, LogOut, UserCircle2, Menu } from "lucide-react";
import { useAuthStore } from "../../store/authStore";

export default function TopNavbar({ onOpenMenu }: { onOpenMenu?: () => void }) {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return (
    <div className="mb-6 flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white px-5 py-4 shadow-soft sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:py-5">
      <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onOpenMenu}
            aria-label="Open navigation menu"
            className="inline-flex h-12 w-12 items-center justify-center rounded-3xl bg-slate-100 text-slate-600 transition hover:bg-slate-200 xl:hidden"
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="hidden h-12 w-12 items-center justify-center rounded-3xl bg-brand-100 text-brand-700 sm:flex">
            <UserCircle2 className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Signed in as</p>
            <p className="text-base font-semibold text-slate-900">{user?.full_name || user?.email || "Medical Professional"}</p>
          </div>
        </div>
        <div className="flex flex-1 items-center gap-3 rounded-3xl bg-slate-50 p-3 sm:max-w-md">
          <Search className="h-4 w-4 text-slate-500" />
          <input
            type="search"
            aria-label="Search patients, reports, predictions"
            placeholder="Search patients, reports, predictions"
            className="w-full bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-500"
          />
        </div>
      </div>
      <div className="flex items-center justify-between gap-3 sm:justify-end">
        <button type="button" onClick={() => alert("You have no new notifications.")} aria-label="Notifications" className="inline-flex h-12 w-12 items-center justify-center rounded-3xl bg-slate-100 text-slate-600 transition hover:bg-slate-200">
          <Bell className="h-5 w-5" />
        </button>
        <button
          type="button"
          onClick={() => void logout()}
          className="inline-flex items-center gap-2 rounded-3xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </div>
    </div>
  );
}
