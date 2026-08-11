import { X } from "lucide-react";

export default function DrugCard({
  drug,
  onRemove,
}: {
  drug: string;
  onRemove?: (drug: string) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-3xl border border-slate-200 bg-white px-4 py-3">
      <div>
        <p className="font-semibold text-slate-900">{drug}</p>
      </div>
      {onRemove ? (
        <button type="button" onClick={() => onRemove(drug)} className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition hover:bg-slate-200">
          <X className="h-4 w-4" />
        </button>
      ) : null}
    </div>
  );
}
