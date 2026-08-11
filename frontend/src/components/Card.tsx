import { ReactNode } from "react";

export default function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft transition hover:-translate-y-0.5 hover:shadow-lg">
      <h2 className="mb-4 text-xl font-semibold text-slate-900">{title}</h2>
      <div className="space-y-4">{children}</div>
    </div>
  );
}
