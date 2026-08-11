import { Outlet, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import AppShell from "./layouts/AppShell";
import LoadingOverlay from "./components/LoadingOverlay";
import OfflineBanner from "./components/OfflineBanner";
import { Toaster } from "react-hot-toast";

function App() {
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const isPublicRoute = location.pathname === "/login" || location.pathname === "/register";

  // Show a brief loading overlay on route change
  useEffect(() => {
    setLoading(true);
    // hide after paint/short delay
    const id = window.setTimeout(() => setLoading(false), 300);
    return () => window.clearTimeout(id);
  }, [location.pathname]);

  return (
    <>
      <OfflineBanner />
      <Toaster 
        position="top-center" 
        toastOptions={{
          className: "text-sm font-medium shadow-lg rounded-2xl border border-slate-100",
          success: {
            iconTheme: { primary: "#10b981", secondary: "#fff" },
            style: { background: "#ecfdf5", color: "#065f46", borderColor: "#a7f3d0" }
          },
          error: {
            iconTheme: { primary: "#ef4444", secondary: "#fff" },
            style: { background: "#fef2f2", color: "#991b1b", borderColor: "#fecaca" }
          },
        }} 
      />
      {isPublicRoute ? (
        <>
          <LoadingOverlay visible={loading} />
          <Outlet />
        </>
      ) : (
        <AppShell>
          <LoadingOverlay visible={loading} />
          <Outlet />
        </AppShell>
      )}
    </>
  );
}

export default App;
