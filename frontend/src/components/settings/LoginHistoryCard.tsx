import { useState, useEffect } from "react";
import Card from "../Card";
import type { User } from "../../types/api";
import { getLoginHistory } from "../../api/settings";

function formatDate(value: string | null) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function LoginHistoryCard({ user }: { user: User | null }) {
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      try {
        const res = await getLoginHistory();
        setHistory(res.data || []);
      } catch (err) {
        console.error("Failed to fetch login history", err);
      } finally {
        setIsLoading(false);
      }
    };
    if (user) fetchHistory();
  }, [user]);

  return (
    <Card title="Login History">
      <div className="space-y-4">
        <p className="text-sm text-slate-500">Recent sign-in activity on your account.</p>
        
        <div className="max-h-64 overflow-y-auto space-y-2 pr-2">
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading history...</p>
          ) : history.length === 0 ? (
            <p className="text-sm text-slate-500">No recent logins found.</p>
          ) : (
            history.map((event) => (
              <div key={event.id} className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 p-3">
                <div>
                  <p className="text-sm font-medium text-slate-900">{event.device || "Unknown Device"}</p>
                  <p className="text-xs text-slate-500">{formatDate(event.created_at)} • IP: {event.ip || "Unknown"}</p>
                </div>
                <div className={`rounded-full px-2 py-1 text-xs font-semibold ${event.successful ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                  {event.successful ? "Success" : "Failed"}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  );
}
