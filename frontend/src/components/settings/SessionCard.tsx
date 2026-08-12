import { useState, useEffect, useMemo } from "react";
import { useAuthStore } from "../../store/authStore";
import Card from "../Card";
import type { User } from "../../types/api";
import { listSessions, revokeSession } from "../../api/settings";
import toast from "react-hot-toast";

function formatDate(value: string | null) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function SessionCard({ user, token }: { user: User | null; token: string | null }) {
  const logout = useAuthStore((state) => state.logout);
  const [sessions, setSessions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchSessions = async () => {
      setIsLoading(true);
      try {
        const res = await listSessions();
        setSessions(res.data || []);
      } catch (err) {
        console.error("Failed to fetch sessions", err);
      } finally {
        setIsLoading(false);
      }
    };
    if (user) fetchSessions();
  }, [user]);

  const handleRevoke = async (id: number) => {
    try {
      await revokeSession(id);
      setSessions(sessions.filter((s) => s.id !== id));
      toast.success("Session revoked successfully");
    } catch (err: any) {
      console.error("Failed to revoke session", err);
      toast.error(err?.response?.data?.detail || "Failed to revoke session");
    }
  };

  const currentLogin = useMemo(() => {
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.iat ? new Date(payload.iat * 1000).toISOString() : null;
    } catch {
      return null;
    }
  }, [token]);

  return (
    <Card title="Active Sessions">
      <div className="space-y-5">
        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Current Login Window</p>
          <p className="mt-2 text-sm font-semibold text-slate-900">{currentLogin ? formatDate(currentLogin) : "Unavailable"}</p>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-700">Other Active Devices</p>
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading sessions...</p>
          ) : sessions.length === 0 ? (
            <p className="text-sm text-slate-500">No other active sessions found.</p>
          ) : (
            sessions.map((session) => (
              <div key={session.id} className="flex items-center justify-between rounded-3xl border border-slate-200 bg-white p-4">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{session.device || "Unknown Device"}</p>
                  <p className="text-xs text-slate-500">IP: {session.ip || "Unknown"} • Last seen: {formatDate(session.last_seen)}</p>
                </div>
                <button
                  onClick={() => handleRevoke(session.id)}
                  className="rounded-xl bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-100 transition"
                >
                  Revoke
                </button>
              </div>
            ))
          )}
        </div>

        {user ? (
          <div className="pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => void logout()}
              className="w-full rounded-2xl bg-red-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-red-700"
            >
              Sign out of this device
            </button>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
