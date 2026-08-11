export type ReportHistoryEntry = {
  id: string;
  patientId: number;
  patientName: string;
  template: string;
  mode: "html" | "pdf";
  url: string;
  viewedAt: string;
  version: number;
  summary: string;
};

const STORAGE_KEY = "medigenie_report_history";
const MAX_HISTORY_ITEMS = 8;

function readHistory(): ReportHistoryEntry[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    return JSON.parse(stored) as ReportHistoryEntry[];
  } catch {
    return [];
  }
}

function writeHistory(history: ReportHistoryEntry[]) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

export function loadReportHistory(): ReportHistoryEntry[] {
  return readHistory().sort((a, b) => new Date(b.viewedAt).getTime() - new Date(a.viewedAt).getTime());
}

export function saveReportHistoryEntry(entry: Omit<ReportHistoryEntry, "id" | "version">) {
  const history = readHistory();
  const nextEntry: ReportHistoryEntry = {
    id: `${entry.patientId}-${Date.now()}`,
    version: history.filter((item) => item.patientId === entry.patientId).length + 1,
    ...entry,
  };

  const nextHistory = [nextEntry, ...history].slice(0, MAX_HISTORY_ITEMS);
  writeHistory(nextHistory);
  return nextHistory;
}

export function clearReportHistory() {
  writeHistory([]);
  return [];
}
