export default function RiskBadge({ risk }: { risk: string }) {
  const isHigh = risk.toLowerCase().includes("high");
  const isMod = risk.toLowerCase().includes("moderate");
  const tone = isHigh
    ? "bg-rose-50 text-rose-700 ring-rose-600/20"
    : isMod
    ? "bg-amber-50 text-amber-700 ring-amber-600/20"
    : "bg-emerald-50 text-emerald-700 ring-emerald-600/20";

  return <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ${tone}`}>
    <span className={`h-1.5 w-1.5 rounded-full ${isHigh ? "bg-rose-500 animate-pulse" : isMod ? "bg-amber-500" : "bg-emerald-500"}`} />
    {risk}
  </span>;
}
