import { useEffect, useState } from "react";
import { WifiOff, Wifi } from "lucide-react";
import toast from "react-hot-toast";

export default function OfflineBanner() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast.success("Internet connection restored.", {
        icon: <Wifi className="h-4 w-4 text-emerald-600" />,
        id: "online-status-toast",
      });
    };

    const handleOffline = () => {
      setIsOnline(false);
      toast.error("Internet connection lost. You are currently offline.", {
        icon: <WifiOff className="h-4 w-4 text-rose-600" />,
        id: "offline-status-toast",
      });
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (isOnline) return null;

  return (
    <div className="sticky top-0 z-[110] flex items-center justify-center gap-2 bg-rose-600 px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-white shadow-md">
      <WifiOff className="h-4 w-4" />
      <span>You are currently offline. Some features and AI services may be unavailable.</span>
    </div>
  );
}
