import { useMemo, useState } from "react";
import { Search, Plus, X } from "lucide-react";

export default function DrugSearch({
  selected,
  onAdd,
  onRemove,
  suggestions,
}: {
  selected: string[];
  onAdd: (medication: string) => void;
  onRemove: (medication: string) => void;
  suggestions: string[];
}) {
  const [query, setQuery] = useState("");
  const normalizedQuery = query.trim().toLowerCase();

  const filteredSuggestions = useMemo(
    () =>
      suggestions
        .filter((item) => !selected.some((selectedValue) => selectedValue.toLowerCase() === item.toLowerCase()))
        .filter((item) => item.toLowerCase().includes(normalizedQuery) && normalizedQuery.length > 0)
        .slice(0, 7),
    [suggestions, selected, normalizedQuery]
  );

  const handleAdd = () => {
    const value = query.trim();
    if (value) {
      onAdd(value);
      setQuery("");
    }
  };

  const canAdd = query.trim().length > 0 && !selected.some((item) => item.toLowerCase() === query.trim().toLowerCase());

  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-slate-700">Search medicines</label>
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleAdd();
              }
            }}
            placeholder="Type medication name"
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-11 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
          />
        </div>
        <button
          type="button"
          onClick={handleAdd}
          disabled={!canAdd}
          className="inline-flex items-center gap-2 rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          <Plus className="h-4 w-4" />
          Add
        </button>
      </div>

      {filteredSuggestions.length ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {filteredSuggestions.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                onAdd(item);
                setQuery("");
              }}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            >
              {item}
            </button>
          ))}
        </div>
      ) : null}

      {selected.length ? (
        <div className="space-y-3 rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-semibold text-slate-900">Selected medications</p>
          <div className="flex flex-wrap gap-2">
            {selected.map((drug) => (
              <button
                key={drug}
                type="button"
                onClick={() => onRemove(drug)}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-100"
              >
                <span>{drug}</span>
                <X className="h-3.5 w-3.5" />
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
          Enter medications above to begin the safety review.
        </div>
      )}
    </div>
  );
}
