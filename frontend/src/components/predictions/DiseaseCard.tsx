import { Link } from "react-router-dom";
import { LucideIcon } from "lucide-react";

export default function DiseaseCard({
  icon: Icon,
  title,
  description,
  inputs,
  to,
  state,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  inputs: string[];
  to: string;
  state?: unknown;
}) {
  return (
    <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-soft transition hover:-translate-y-1 hover:shadow-lg">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-2xl">{Icon ? <Icon className="inline-block h-10 w-10 rounded-2xl bg-brand-50 p-2 text-brand-600" /> : null}</p>
          <h3 className="mt-4 text-xl font-semibold text-slate-900">{title}</h3>
        </div>
        <div className="rounded-3xl bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-600">AI model</div>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-600">{description}</p>
      <div className="mt-6 space-y-2">
        <p className="text-sm font-semibold text-slate-900">Required inputs</p>
        <ul className="grid gap-2 text-sm text-slate-500 sm:grid-cols-2">
          {inputs.map((item) => (
            <li key={item} className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2">
              {item}
            </li>
          ))}
        </ul>
      </div>
      <Link
        to={to}
        state={state}
        className="mt-6 inline-flex w-full items-center justify-center rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
      >
        Start prediction
      </Link>
    </div>
  );
}
