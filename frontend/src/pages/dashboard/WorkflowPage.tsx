import { useState, useEffect } from "react";
import {
  Brain,
  Shield,
  Star,
  BookOpen,
  Zap,
  Database,
  ChevronDown,
  ChevronRight,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  Award,
  FileText,
  RefreshCw,
} from "lucide-react";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface PromptEntry {
  name: string;
  category: string;
  active_version: number;
  total_versions: number;
  variables: string[];
  description: string;
}

interface TestDetail {
  test: string;
  passed: boolean;
  failures: string[];
  rendered_length?: number;
}

interface PromptTestResult {
  prompt_name: string;
  version: number;
  score: number;
  passed: number;
  failed: number;
  total: number;
  details: TestDetail[];
  status: "PASS" | "FAIL";
}

interface QualitySummary {
  agent: string;
  runs: number;
  mean_quality: number;
  last_grade: string;
  mean_latency?: number;
  failure_rate?: number;
}

interface LeaderboardEntry {
  rank: number;
  agent: string;
  runs: number;
  composite_score: number;
  quality_score: number;
  mean_latency_s: number;
  failure_rate: number;
  guardrail_pass_rate: number;
  grade: string;
}

interface GuardrailViolation {
  timestamp: string;
  agent: string;
  passed: boolean;
  violations: { guard: string; severity: string; message: string }[];
}

interface MemoryTelemetry {
  run_id: string;
  timestamp: string;
  state_size_bytes: number;
  pruned_knowledge_results: number;
  compressed_fields: string[];
  cache_hit: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1") + "/workflow";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(API_BASE + path, options);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function gradeColor(grade: string): string {
  switch (grade) {
    case "A": return "text-emerald-500";
    case "B": return "text-blue-500";
    case "C": return "text-amber-500";
    case "D": return "text-orange-500";
    default:  return "text-rose-500";
  }
}

function gradeBg(grade: string): string {
  switch (grade) {
    case "A": return "bg-emerald-100 text-emerald-700 border-emerald-200";
    case "B": return "bg-blue-100 text-blue-700 border-blue-200";
    case "C": return "bg-amber-100 text-amber-700 border-amber-200";
    case "D": return "bg-orange-100 text-orange-700 border-orange-200";
    default:  return "bg-rose-100 text-rose-700 border-rose-200";
  }
}

function severityBg(severity: string): string {
  switch (severity) {
    case "CRITICAL": return "bg-rose-100 text-rose-700 border-rose-200";
    case "HIGH":     return "bg-orange-100 text-orange-700 border-orange-200";
    case "MEDIUM":   return "bg-amber-100 text-amber-700 border-amber-200";
    default:         return "bg-slate-100 text-slate-600 border-slate-200";
  }
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.9 ? "bg-emerald-500" : score >= 0.75 ? "bg-blue-500" : score >= 0.6 ? "bg-amber-500" : "bg-rose-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 rounded-full bg-slate-100">
        <div className={`h-2 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 text-right text-xs font-semibold text-slate-600">{pct}%</span>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab: Prompt Manager
// ─────────────────────────────────────────────────────────────────────────────

function PromptManager() {
  const [prompts, setPrompts] = useState<PromptEntry[]>([]);
  const [testResult, setTestResult] = useState<Record<string, PromptTestResult>>({});
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch<{ prompts: PromptEntry[] }>("/prompts").then((d) => {
      if (d) setPrompts(d.prompts);
    });
  }, []);

  const runTest = async (name: string) => {
    setLoading(true);
    const result = await apiFetch<PromptTestResult>(`/prompts/${name}/test`, { method: "POST" });
    if (result) setTestResult((prev) => ({ ...prev, [name]: result }));
    setLoading(false);
  };

  const runAll = async () => {
    setLoading(true);
    const result = await apiFetch<{ results: { prompt_name: string; score: number; passed: number; failed: number; total: number; details: TestDetail[]; version: number }[] }>("/prompts/test-all", { method: "POST" });
    if (result) {
      const map: Record<string, PromptTestResult> = {};
      result.results.forEach((r) => {
        map[r.prompt_name] = { ...r, status: r.score >= 0.8 ? "PASS" : "FAIL", prompt_name: r.prompt_name };
      });
      setTestResult(map);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{prompts.length} registered prompts across all agents</p>
        <button
          onClick={runAll}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Run All Tests
        </button>
      </div>

      <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 bg-white overflow-hidden">
        {prompts.map((p) => {
          const result = testResult[p.name];
          const isExpanded = expanded === p.name;
          return (
            <div key={p.name}>
              <button
                onClick={() => setExpanded(isExpanded ? null : p.name)}
                className="flex w-full items-center gap-4 p-4 text-left hover:bg-slate-50 transition"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50">
                  <FileText className="h-4 w-4 text-indigo-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="truncate font-semibold text-slate-900">{p.name}</p>
                  <p className="text-xs text-slate-400">{p.category} · v{p.active_version} of {p.total_versions}</p>
                </div>
                {result && (
                  <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-bold ${result.status === "PASS" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-rose-50 text-rose-700 border-rose-200"}`}>
                    {result.status} {result.score >= 0 && `${Math.round(result.score * 100)}%`}
                  </span>
                )}
                {isExpanded ? <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" /> : <ChevronRight className="h-4 w-4 text-slate-400 shrink-0" />}
              </button>

              {isExpanded && (
                <div className="border-t border-slate-100 bg-slate-50 p-4 space-y-3">
                  <div className="flex flex-wrap gap-2 text-xs">
                    {p.variables.map((v) => (
                      <span key={v} className="rounded-full bg-indigo-100 px-2.5 py-0.5 font-mono text-indigo-700">{`{{${v}}}`}</span>
                    ))}
                  </div>
                  {p.description && <p className="text-sm text-slate-600">{p.description}</p>}

                  {result && (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Test Results</p>
                      {result.details.map((d, i) => (
                        <div key={i} className={`flex items-start gap-2 rounded-xl p-3 ${d.passed ? "bg-emerald-50" : "bg-rose-50"}`}>
                          {d.passed ? <CheckCircle className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" /> : <XCircle className="h-4 w-4 text-rose-500 mt-0.5 shrink-0" />}
                          <div>
                            <p className="text-xs font-semibold text-slate-800">{d.test}</p>
                            {d.failures.map((f, j) => <p key={j} className="text-xs text-rose-600">{f}</p>)}
                            {d.rendered_length && <p className="text-xs text-slate-400">{d.rendered_length} chars rendered</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <button
                    onClick={() => runTest(p.name)}
                    disabled={loading}
                    className="rounded-xl bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 transition"
                  >
                    {loading ? "Running…" : "Run Tests"}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab: Agent Evaluation Leaderboard
// ─────────────────────────────────────────────────────────────────────────────

function EvaluationLeaderboard() {
  const [data, setData] = useState<{ leaderboard: LeaderboardEntry[]; total_agents: number } | null>(null);

  useEffect(() => {
    apiFetch<{ leaderboard: LeaderboardEntry[]; total_agents: number }>("/evaluation").then(setData);
  }, []);

  if (!data) {
    return (
      <div className="flex h-40 items-center justify-center text-slate-400">
        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
        Loading evaluation data…
      </div>
    );
  }

  if (data.leaderboard.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-slate-200 text-slate-400">
        No evaluation data yet. Run a prediction to populate the leaderboard.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
      <table className="w-full text-sm min-w-[600px]">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50">
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400">#</th>
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400">Agent</th>
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400">Grade</th>
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400">Quality</th>
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400 hidden sm:table-cell">Latency</th>
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400 hidden md:table-cell">Failure Rate</th>
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400 hidden md:table-cell">Guardrails</th>
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400">Runs</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {data.leaderboard.map((e) => (
            <tr key={e.agent} className="hover:bg-slate-50 transition">
              <td className="p-3 font-bold text-slate-400">{e.rank}</td>
              <td className="p-3">
                <div className="flex items-center gap-2">
                  {e.rank === 1 && <Award className="h-4 w-4 text-amber-500" />}
                  <span className="font-semibold text-slate-800">{e.agent.replace("Agent", "")}</span>
                </div>
              </td>
              <td className="p-3">
                <span className={`rounded-full border px-2.5 py-0.5 text-xs font-bold ${gradeBg(e.grade)}`}>{e.grade}</span>
              </td>
              <td className="p-3 w-36">
                <ScoreBar score={e.quality_score} />
              </td>
              <td className="p-3 text-slate-600 hidden sm:table-cell">{e.mean_latency_s.toFixed(3)}s</td>
              <td className="p-3 hidden md:table-cell">
                <span className={`text-xs font-semibold ${e.failure_rate > 0.1 ? "text-rose-600" : "text-emerald-600"}`}>
                  {Math.round(e.failure_rate * 100)}%
                </span>
              </td>
              <td className="p-3 hidden md:table-cell">
                <span className={`text-xs font-semibold ${e.guardrail_pass_rate >= 0.9 ? "text-emerald-600" : "text-amber-600"}`}>
                  {Math.round(e.guardrail_pass_rate * 100)}%
                </span>
              </td>
              <td className="p-3 text-slate-500">{e.runs}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab: Guardrails Feed
// ─────────────────────────────────────────────────────────────────────────────

function GuardrailsFeed() {
  const [data, setData] = useState<{ violations: GuardrailViolation[]; stats: Record<string, unknown> } | null>(null);

  useEffect(() => {
    apiFetch<{ violations: GuardrailViolation[]; stats: Record<string, unknown> }>("/guardrails/log").then(setData);
  }, []);

  if (!data) return <div className="flex h-40 items-center justify-center text-slate-400"><RefreshCw className="mr-2 h-4 w-4 animate-spin" />Loading…</div>;

  const stats = data.stats as { total_checks?: number; total_violations?: number; passed_rate?: number };

  return (
    <div className="space-y-4">
      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Total Checks", value: stats.total_checks ?? 0, color: "text-slate-700" },
          { label: "Violations", value: stats.total_violations ?? 0, color: "text-rose-600" },
          { label: "Pass Rate", value: `${Math.round((stats.passed_rate ?? 1) * 100)}%`, color: "text-emerald-600" },
        ].map((s) => (
          <div key={s.label} className="rounded-2xl border border-slate-200 bg-white p-4 text-center">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="mt-1 text-xs text-slate-400">{s.label}</p>
          </div>
        ))}
      </div>

      {data.violations.length === 0 ? (
        <div className="flex h-32 items-center justify-center rounded-2xl border border-dashed border-emerald-200 bg-emerald-50 text-emerald-600">
          <CheckCircle className="mr-2 h-5 w-5" />
          No guardrail violations recorded
        </div>
      ) : (
        <div className="space-y-2">
          {data.violations.map((v, i) => (
            <div key={i} className={`rounded-2xl border p-4 ${v.passed ? "border-slate-100 bg-white" : "border-rose-100 bg-rose-50"}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {v.passed ? <CheckCircle className="h-4 w-4 text-emerald-500" /> : <AlertTriangle className="h-4 w-4 text-rose-500" />}
                  <span className="font-semibold text-sm text-slate-800">{v.agent}</span>
                </div>
                <span className="text-xs text-slate-400">{new Date(v.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {v.violations.map((viol, j) => (
                  <span key={j} className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${severityBg(viol.severity)}`}>
                    [{viol.severity}] {viol.message}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab: Memory Telemetry
// ─────────────────────────────────────────────────────────────────────────────

function MemoryDashboard() {
  const [data, setData] = useState<{ telemetry: MemoryTelemetry[]; cache_stats: Record<string, unknown> } | null>(null);

  useEffect(() => {
    apiFetch<{ telemetry: MemoryTelemetry[]; cache_stats: Record<string, unknown> }>("/memory").then(setData);
  }, []);

  if (!data) return <div className="flex h-40 items-center justify-center text-slate-400"><RefreshCw className="mr-2 h-4 w-4 animate-spin" />Loading…</div>;

  const cache = data.cache_stats as { size?: number; max_size?: number; hit_rate?: number; hits?: number; misses?: number };

  return (
    <div className="space-y-4">
      {/* Cache stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Cached Sessions", value: `${cache.size ?? 0} / ${cache.max_size ?? 50}`, color: "text-blue-600" },
          { label: "Cache Hit Rate", value: `${Math.round((cache.hit_rate ?? 0) * 100)}%`, color: "text-emerald-600" },
          { label: "Cache Hits", value: cache.hits ?? 0, color: "text-slate-700" },
          { label: "Cache Misses", value: cache.misses ?? 0, color: "text-amber-600" },
        ].map((s) => (
          <div key={s.label} className="rounded-2xl border border-slate-200 bg-white p-4 text-center">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="mt-1 text-xs text-slate-400">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Telemetry log */}
      {data.telemetry.length === 0 ? (
        <div className="flex h-32 items-center justify-center rounded-2xl border border-dashed border-slate-200 text-slate-400">
          No memory telemetry yet. Run a prediction to populate.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
          <table className="w-full text-sm min-w-[600px]">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400">Run</th>
                <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400">State Size</th>
                <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400 hidden sm:table-cell">Pruned</th>
                <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400 hidden md:table-cell">Compressed</th>
                <th className="p-3 text-left text-xs font-semibold uppercase tracking-widest text-slate-400">Cache</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {data.telemetry.map((t) => (
                <tr key={t.run_id} className="hover:bg-slate-50">
                  <td className="p-3 font-mono text-xs text-slate-600">{t.run_id}</td>
                  <td className="p-3">
                    <span className="text-xs font-semibold text-slate-800">{(t.state_size_bytes / 1024).toFixed(1)} KB</span>
                  </td>
                  <td className="p-3 hidden sm:table-cell text-xs text-slate-500">{t.pruned_knowledge_results} results</td>
                  <td className="p-3 hidden md:table-cell">
                    <div className="flex flex-wrap gap-1">
                      {t.compressed_fields.map((f) => (
                        <span key={f} className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700">{f}</span>
                      ))}
                      {t.compressed_fields.length === 0 && <span className="text-xs text-slate-400">—</span>}
                    </div>
                  </td>
                  <td className="p-3">
                    {t.cache_hit
                      ? <span className="text-xs font-semibold text-emerald-600">HIT</span>
                      : <span className="text-xs text-slate-400">MISS</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab: Citation Verifier
// ─────────────────────────────────────────────────────────────────────────────

function CitationVerifierPanel() {
  const [input, setInput] = useState(`[
  {"id": "12345678", "type": "pubmed", "source": "PubMed"},
  {"id": "10.1056/NEJMoa2034577", "type": "doi"},
  {"id": "ADA-2024-Standards", "type": "guideline", "source": "ADA"},
  {"id": "https://who.int/diabetes-guidelines", "type": "url"}
]`);
  const [result, setResult] = useState<{ total: number; verified: number; unverified: number; invalid: number; confidence_score: number; verdicts: { citation_id: string; source_type: string; status: string; detail: string }[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const verify = async () => {
    setError("");
    setLoading(true);
    try {
      const parsed = JSON.parse(input);
      const res = await apiFetch<typeof result>("/citations/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ citations: parsed }),
      });
      setResult(res);
    } catch {
      setError("Invalid JSON format. Please check your input.");
    }
    setLoading(false);
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "VERIFIED": return "bg-emerald-100 text-emerald-700 border-emerald-200";
      case "UNVERIFIED": return "bg-amber-100 text-amber-700 border-amber-200";
      default: return "bg-rose-100 text-rose-700 border-rose-200";
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <label className="mb-2 block text-xs font-semibold uppercase tracking-widest text-slate-400">
          Citations JSON
        </label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={8}
          className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-mono text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        {error && <p className="mt-1 text-xs text-rose-600">{error}</p>}
        <button
          onClick={verify}
          disabled={loading}
          className="mt-3 flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 transition"
        >
          <Shield className={`h-4 w-4 ${loading ? "animate-pulse" : ""}`} />
          {loading ? "Verifying…" : "Verify Citations"}
        </button>
      </div>

      {result && (
        <div className="space-y-3">
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: "Total", value: result.total, color: "text-slate-700" },
              { label: "Verified", value: result.verified, color: "text-emerald-600" },
              { label: "Unverified", value: result.unverified, color: "text-amber-600" },
              { label: "Invalid", value: result.invalid, color: "text-rose-600" },
            ].map((s) => (
              <div key={s.label} className="rounded-2xl border border-slate-200 bg-white p-3 text-center">
                <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
                <p className="mt-0.5 text-xs text-slate-400">{s.label}</p>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-700">Confidence Score</p>
              <span className={`text-lg font-bold ${gradeColor(result.confidence_score >= 0.9 ? "A" : result.confidence_score >= 0.7 ? "B" : "D")}`}>
                {Math.round(result.confidence_score * 100)}%
              </span>
            </div>
            <ScoreBar score={result.confidence_score} />
          </div>

          <div className="space-y-2">
            {result.verdicts.map((v, i) => (
              <div key={i} className="flex items-start gap-3 rounded-2xl border border-slate-100 bg-white p-3">
                <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-bold ${statusColor(v.status)}`}>{v.status}</span>
                <div>
                  <p className="text-xs font-semibold text-slate-800 font-mono">{v.citation_id}</p>
                  <p className="text-xs text-slate-500">{v.source_type} · {v.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

const TABS = [
  { id: "prompts",     label: "Prompt Manager",   icon: FileText },
  { id: "evaluation",  label: "Agent Evaluation",  icon: Award },
  { id: "guardrails",  label: "Guardrails",         icon: Shield },
  { id: "citations",   label: "Citation Verifier",  icon: BookOpen },
  { id: "memory",      label: "Memory",             icon: Database },
] as const;

type TabId = typeof TABS[number]["id"];

export default function WorkflowPage() {
  const [activeTab, setActiveTab] = useState<TabId>("prompts");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
            <Brain className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">AI Workflow Intelligence</h1>
            <p className="text-sm text-slate-500">Phase 8 — Prompt versioning, evaluation, guardrails, citation verification & memory management</p>
          </div>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex flex-wrap gap-1 rounded-2xl border border-slate-200 bg-slate-100/50 p-1">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition ${
                active
                  ? "bg-white text-indigo-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === "prompts"    && <PromptManager />}
        {activeTab === "evaluation" && <EvaluationLeaderboard />}
        {activeTab === "guardrails" && <GuardrailsFeed />}
        {activeTab === "citations"  && <CitationVerifierPanel />}
        {activeTab === "memory"     && <MemoryDashboard />}
      </div>
    </div>
  );
}
