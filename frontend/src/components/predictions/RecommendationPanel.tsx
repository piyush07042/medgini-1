export default function RecommendationPanel({ recommendations }: { recommendations?: Array<Record<string, any>> | null }) {
  if (!recommendations?.length) {
    return <p className="text-sm text-slate-500">No recommendations were returned.</p>;
  }

  return (
    <div className="space-y-4">
      {recommendations.map((item, index) => {
        const title = typeof item === "object" ? item.title || item.priority || `Recommendation ${index + 1}` : `Recommendation ${index + 1}`;
        const text = typeof item === "object" ? item.recommendation || JSON.stringify(item) : String(item);
        const category = typeof item === "object" ? item.category || item.type || "General" : "General";

        return (
          <div key={index} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-900">{title}</p>
              <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">{category}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-700">{text}</p>
          </div>
        );
      })}
    </div>
  );
}
