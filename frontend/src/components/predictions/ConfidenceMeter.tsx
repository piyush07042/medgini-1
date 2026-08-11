export default function ConfidenceMeter({ confidence, compact = false }: { confidence: number; compact?: boolean }) {
  const percent = Math.round(confidence * 100);
  const width = `${Math.min(100, Math.max(0, percent))}%`;
  const isHigh = percent >= 80;
  const isMod = percent >= 60;
  const tone = isHigh ? "bg-emerald-500 shadow-emerald-500/40" : isMod ? "bg-amber-500 shadow-amber-500/40" : "bg-rose-500 shadow-rose-500/40";
  const textTone = isHigh ? "text-emerald-700" : isMod ? "text-amber-700" : "text-rose-700";

  if (compact) {
    return (
      <div className="flex items-center gap-3 text-sm">
        <div className="h-2.5 w-28 overflow-hidden rounded-full bg-slate-100 ring-1 ring-inset ring-slate-200">
          <div className={`h-full rounded-full shadow-[0_0_10px_rgba(0,0,0,0.2)] transition-all duration-1000 ease-out ${tone}`} style={{ width }} />
        </div>
        <div className={`text-xs font-bold tracking-wide ${textTone}`}>{percent}%</div>
      </div>
    );
  }

  return (
    <div className="space-y-2 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-700">Confidence Score</span>
        <span className={`font-bold tracking-wide ${textTone}`}>{percent}%</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100 ring-1 ring-inset ring-slate-200">
        <div className={`h-full rounded-full shadow-[0_0_12px_rgba(0,0,0,0.3)] transition-all duration-1000 ease-out ${tone}`} style={{ width }} />
      </div>
    </div>
  );
}
