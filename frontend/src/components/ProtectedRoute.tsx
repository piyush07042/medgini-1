import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export default function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-4xl space-y-6 rounded-3xl border border-slate-200 bg-white p-8 shadow-soft">
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 animate-pulse rounded-full bg-slate-200" />
            <div className="space-y-2">
              <div className="h-4 w-48 animate-pulse rounded bg-slate-200" />
              <div className="h-3 w-32 animate-pulse rounded bg-slate-100" />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="h-28 animate-pulse rounded-2xl bg-slate-100" />
            <div className="h-28 animate-pulse rounded-2xl bg-slate-100" />
            <div className="h-28 animate-pulse rounded-2xl bg-slate-100" />
          </div>
          <div className="space-y-3">
            <div className="h-10 w-full animate-pulse rounded-xl bg-slate-100" />
            <div className="h-10 w-full animate-pulse rounded-xl bg-slate-100" />
            <div className="h-10 w-full animate-pulse rounded-xl bg-slate-100" />
          </div>
          <div className="text-center text-xs font-medium text-slate-400">
            MediGenie AI CDSS • Loading System Components...
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
