import { Link, useNavigate } from "react-router-dom";
import { Stethoscope, ArrowLeft, Home, FileSearch } from "lucide-react";

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center px-4 py-12 text-center">
      <div className="relative mb-6 flex h-24 w-24 items-center justify-center rounded-3xl bg-brand-50 text-brand-600 shadow-sm ring-8 ring-brand-50/50">
        <Stethoscope className="h-12 w-12" />
        <span className="absolute -right-2 -top-2 flex h-8 w-8 items-center justify-center rounded-full bg-rose-500 text-xs font-bold text-white shadow">
          404
        </span>
      </div>
      
      <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Page Not Found</h1>
      <p className="mt-3 max-w-md text-sm leading-6 text-slate-600">
        The clinical page or patient document you requested couldn't be located. It may have been moved or deleted.
      </p>

      <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          <ArrowLeft className="h-4 w-4" />
          Go Back
        </button>
        <Link
          to="/"
          className="inline-flex items-center justify-center gap-2 rounded-2xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          <Home className="h-4 w-4" />
          Return to Dashboard
        </Link>
        <Link
          to="/patients"
          className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          <FileSearch className="h-4 w-4" />
          Patient Directory
        </Link>
      </div>
    </div>
  );
}
