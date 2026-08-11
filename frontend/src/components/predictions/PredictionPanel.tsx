import { type ReactNode } from "react";

export default function PredictionPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
      <h3 className="mb-4 text-lg font-semibold text-slate-900">{title}</h3>
      {children}
    </div>
  );
}
