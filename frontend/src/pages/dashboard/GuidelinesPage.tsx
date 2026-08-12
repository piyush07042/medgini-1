import { useEffect, useState } from "react";
import { BookOpen, RefreshCw, FileText, CheckCircle, HelpCircle } from "lucide-react";
import PageHeading from "../../components/PageHeading";
import Card from "../../components/Card";

interface GuidelineMetadata {
  disease_key: string;
  disease_name: string;
  source: string;
  organization: string;
  version: string;
  sections_count: number;
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1") + "/guidelines";

export default function GuidelinesPage() {
  const [guidelines, setGuidelines] = useState<GuidelineMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchGuidelines = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/list`);
      if (!res.ok) throw new Error("Failed to load clinical guidelines inventory.");
      const data = await res.json();
      if (data.success) {
        setGuidelines(data.guidelines || []);
      } else {
        throw new Error(data.message || "Unable to fetch guidelines");
      }
    } catch (e: any) {
      setError(e.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGuidelines();
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <PageHeading
          title="Clinical Guidelines Repository"
          description="Browse and review evidence-based clinical guidelines integrated across all 9 disease risk classifiers."
        />
        <button
          onClick={fetchGuidelines}
          className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh Registry
        </button>
      </div>

      {/* Intro Banner */}
      <div className="flex flex-col gap-6 rounded-3xl bg-gradient-to-r from-slate-900 to-indigo-950 p-7 text-white shadow-xl md:flex-row md:items-center">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-indigo-300 ring-1 ring-white/10">
          <BookOpen className="h-9 w-9" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Evidence-Based Clinical Decision Support (CDSS)</h2>
          <p className="mt-1 max-w-3xl text-sm text-indigo-200">
            MediGenie aligns diagnostic output with authoritative protocols from the world's leading medical boards (ADA, AHA, KDIGO, WHO, etc.). 
            The CDS engine reads risk probabilities, patient history, and laboratory values to compile tailored precautions, follow-up schedules, and contraindications.
          </p>
        </div>
      </div>

      {/* Grid of guideline items */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-4">Supported Guidelines Inventory</h3>
        {loading && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-32 animate-pulse rounded-3xl bg-slate-100" />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-center text-sm text-rose-700">
            <p className="font-semibold">Unable to load clinical guidelines</p>
            <p className="mt-1">{error}</p>
          </div>
        )}

        {!loading && !error && guidelines.length === 0 && (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-500">
            No clinical guidelines loaded. Ensure the backend directory is populated.
          </div>
        )}

        {!loading && !error && guidelines.length > 0 && (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {guidelines.map((g) => (
              <div key={g.disease_key} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft hover:shadow-md transition">
                <div className="flex items-start justify-between">
                  <div className="rounded-2xl bg-indigo-50/50 p-2.5 text-indigo-600">
                    <FileText className="h-6 w-6" />
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
                    v{g.version}
                  </span>
                </div>
                <h4 className="mt-4 text-base font-bold text-slate-900">{g.disease_name}</h4>
                <p className="mt-1 text-xs text-slate-500 font-semibold">{g.organization}</p>
                <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Source: <strong className="text-slate-700">{g.source}</strong></span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Card title="Guideline-Directed Medical Therapy (GDMT)">
        <div className="space-y-4 text-sm text-slate-700">
          <p>
            The Clinical Knowledge Layer ensures patient safety by vetting therapeutic decisions against specific clinical exclusions.
          </p>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
              <p className="font-semibold text-slate-900 flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4 text-indigo-600" />
                Rule-Based Exclusions
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Checks patient metabolic indicators (e.g. eGFR thresholds) before recommending critical medications.
              </p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
              <p className="font-semibold text-slate-900 flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4 text-indigo-600" />
                Dynamic Follow-up
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Calculates and schedules clinical checkups, lab panels, and screenings based on matched guidelines.
              </p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
              <p className="font-semibold text-slate-900 flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4 text-indigo-600" />
                Traceable Audit
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Maintains specific citations and versions attached directly to prediction history records.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
