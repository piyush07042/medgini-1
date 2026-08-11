import { ReactNode, useState, useEffect } from "react";
import Sidebar from "../components/dashboard/Sidebar";
import TopNavbar from "../components/dashboard/TopNavbar";

export default function AppShell({ children }: { children: ReactNode }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isMobileMenuOpen]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto flex min-h-screen max-w-[1500px] gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <Sidebar isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />
        <main className="flex-1 flex flex-col min-w-0">
          <TopNavbar onOpenMenu={() => setIsMobileMenuOpen(true)} />
          <div className="flex-1 overflow-hidden">
            <div className="min-h-screen rounded-3xl border border-slate-200 bg-white px-6 py-6 shadow-soft sm:px-8 sm:py-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
