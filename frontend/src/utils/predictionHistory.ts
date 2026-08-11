export type PredictionHistoryItem = {
  id: string;
  patientId: number;
  disease: string;
  createdAt: string;
  prediction: number | string;
  probability: number;
  confidence: number;
  confidenceLabel?: string | null;
  summary?: string;
  result: Record<string, any>;
};

const STORAGE_KEY = "medigenie_prediction_history";

function readHistory(): PredictionHistoryItem[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    return JSON.parse(stored) as PredictionHistoryItem[];
  } catch {
    return [];
  }
}

function writeHistory(history: PredictionHistoryItem[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

export function getPredictionHistory(patientId: number): PredictionHistoryItem[] {
  return readHistory().filter((item) => item.patientId === patientId).sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
}

export function addPredictionHistory(entry: PredictionHistoryItem) {
  const history = readHistory();
  writeHistory([entry, ...history].slice(0, 50));
}
