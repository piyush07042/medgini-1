export default function DrugSafetyPanel({ drugSafety }: { drugSafety?: Record<string, any> | null }) {
  if (!drugSafety || Object.keys(drugSafety).length === 0) {
    return <p className="text-sm text-slate-500">No drug safety information was returned.</p>;
  }

  return (
    <div className="space-y-4">
      {Object.entries(drugSafety).map(([key, value]) => (
        <div key={key} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-semibold text-slate-900">{key.replace(/_/g, " ")}</p>
          <pre className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{typeof value === "string" ? value : JSON.stringify(value, null, 2)}</pre>
        </div>
      ))}
    </div>
  );
}
