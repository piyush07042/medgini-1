export default function InteractionSeverity({ severity }: { severity: string }) {
  const classes =
    severity === "High"
      ? "bg-red-100 text-red-700"
      : severity === "Medium"
      ? "bg-amber-100 text-amber-700"
      : "bg-emerald-100 text-emerald-700";

  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] ${classes}`}>{severity}</span>;
}
