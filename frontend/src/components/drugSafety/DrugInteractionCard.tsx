import InteractionSeverity from "./InteractionSeverity";

export default function DrugInteractionCard({
  interaction,
}: {
  interaction: {
    drugs_involved: string[];
    severity: string;
    explanation: string;
    recommendation: string;
  };
}) {
  const isHigh = interaction.severity.toLowerCase().includes("high") || interaction.severity.toLowerCase().includes("severe");
  const isMod = interaction.severity.toLowerCase().includes("moderate");
  const cardTone = isHigh ? "border-rose-200 bg-rose-50/50" : isMod ? "border-amber-200 bg-amber-50/50" : "border-emerald-200 bg-emerald-50/50";

  return (
    <div className={`rounded-3xl border p-5 transition-shadow hover:shadow-sm ${cardTone}`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-900">{interaction.drugs_involved.join(" ↔ ")}</p>
          <p className="mt-2 text-sm text-slate-600">{interaction.explanation}</p>
        </div>
        <InteractionSeverity severity={interaction.severity} />
      </div>
      <div className="mt-4 rounded-2xl border border-white/50 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
        <p className="text-sm font-semibold text-slate-900">Recommendation</p>
        <p className="mt-2 text-sm leading-6 text-slate-700">{interaction.recommendation}</p>
      </div>
    </div>
  );
}
