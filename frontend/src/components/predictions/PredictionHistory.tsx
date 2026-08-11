import { useMemo, useState } from "react";
import type { PredictionHistoryItem } from "../../utils/predictionHistory";

export default function PredictionHistory({ history }: { history: PredictionHistoryItem[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selectedItem = useMemo(() => {
    if (!history.length) return null;
    return history.find((item) => item.id === selectedId) ?? history[0];
  }, [history, selectedId]);

  if (!history.length) {
    return <p className="text-sm text-slate-500">No previous predictions are available for this patient.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {history.slice(0, 4).map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setSelectedId(item.id)}
            className={`rounded-full px-3 py-2 text-sm font-semibold transition ${selectedItem?.id === item.id ? "bg-brand-600 text-white" : "bg-white text-slate-700 ring-1 ring-slate-200"}`}
          >
            {item.disease}
          </button>
        ))}
      </div>

      <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-semibold text-slate-900">{selectedItem?.disease}</p>
            <p className="text-sm text-slate-500">{selectedItem ? new Date(selectedItem.createdAt).toLocaleString() : ""}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
            <span>Prediction: {selectedItem?.prediction}</span>
            <span>Probability: {selectedItem?.probability.toFixed(2)}</span>
            <span>Confidence: {Math.round((selectedItem?.confidence ?? 0) * 100)}%</span>
            {selectedItem?.confidenceLabel ? <span>{selectedItem.confidenceLabel}</span> : null}
          </div>
        </div>
        {selectedItem?.summary ? <p className="mt-3 text-sm text-slate-700">{selectedItem.summary}</p> : null}
      </div>

      {history.length > 1 ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-4">
          <p className="text-sm font-semibold text-slate-900">Compare with prior runs</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {history.slice(1).map((item) => (
              <div key={item.id} className="rounded-2xl bg-slate-50 p-3 text-sm text-slate-600">
                <p className="font-semibold text-slate-900">{item.disease}</p>
                <p className="mt-1">Prediction {item.prediction}</p>
                <p>Probability {item.probability.toFixed(2)}</p>
                <p>Confidence {Math.round(item.confidence * 100)}%</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
