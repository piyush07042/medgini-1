import { Loader2 } from "lucide-react";

export default function LoadingOverlay({ visible }: { visible: boolean }) {
  if (!visible) return null;
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm transition-all duration-300">
      <div className="flex flex-col items-center justify-center rounded-3xl border border-white/20 bg-white/90 px-8 py-6 shadow-2xl backdrop-blur-md">
        <Loader2 className="h-10 w-10 animate-spin text-brand-600" />
        <p className="mt-4 text-sm font-semibold text-slate-800">Loading MediGenie...</p>
      </div>
    </div>
  );
}
