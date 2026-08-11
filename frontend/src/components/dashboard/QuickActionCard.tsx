import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

export default function QuickActionCard({ title, subtitle, to }: { title: string; subtitle: string; to: string }) {
  return (
    <Link to={to} className="group block rounded-2xl border border-slate-100 bg-white px-4 py-3 transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
        </div>
        <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-600 text-white transition group-hover:from-brand-600 group-hover:to-brand-700">
          <ArrowRight className="h-4 w-4" />
        </div>
      </div>
    </Link>
  );
}
