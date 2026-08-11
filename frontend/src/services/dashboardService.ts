import { fetchDashboard, type DashboardPayload } from "../api/dashboard";
export type DashboardStat = {
  title: string;
  value: string;
  trend: string;
  positive: boolean;
  label: string;
};

export type RecentPatient = {
  id: number;
  name: string;
  age: number;
  gender: string;
  lastVisit: string;
};

export type RecentReport = {
  id: number;
  filename: string;
  uploadedAt: string;
  status: "Completed" | "Pending" | "Review";
};

export type RecentPrediction = {
  id: number;
  patient: string;
  disease: string;
  risk: "Low" | "Moderate" | "High" | "Critical";
  confidence: string;
  date: string;
};

export type SystemStatusItem = {
  service: string;
  status: "Online" | "Degraded" | "Offline";
  description: string;
};

export type ActivityEvent = {
  id: number;
  title: string;
  description: string;
  time: string;
};

export type PieSlice = {
  name: string;
  value: number;
};

export type LinePoint = {
  month: string;
  predictions: number;
  reports: number;
};

export type BarSlice = {
  category: string;
  value: number;
};

export type AreaData = {
  month: string;
  generated: number;
};

function normalizeRisk(value: string | undefined): RecentPrediction["risk"] {
  const normalized = (value ?? "Moderate").toLowerCase();
  if (normalized.includes("critical")) return "Critical";
  if (normalized.includes("high")) return "High";
  if (normalized.includes("low")) return "Low";
  return "Moderate";
}

function formatConfidence(probability: number, label?: string | null): string {
  if (label) return label;
  if (!Number.isFinite(probability)) return "N/A";
  const percent = probability <= 1 ? probability * 100 : probability;
  return `${Math.round(percent)}%`;
}

let dashboardCache: Promise<DashboardPayload> | null = null;

export async function getDashboardData(forceRefresh = false): Promise<DashboardPayload> {
  if (!dashboardCache || forceRefresh) {
    dashboardCache = fetchDashboard();
  }
  return dashboardCache;
}

export async function getDashboardStats(): Promise<DashboardStat[]> {
  return (await getDashboardData()).stats;
}

export async function getRecentPatients(): Promise<RecentPatient[]> {
  return (await getDashboardData()).recent_patients;
}

export async function getRecentReports(): Promise<RecentReport[]> {
  return (await getDashboardData()).recent_reports;
}

export async function getRecentPredictions(): Promise<RecentPrediction[]> {
  return (await getDashboardData()).recent_predictions;
}

export async function getSystemStatus(): Promise<SystemStatusItem[]> {
  return (await getDashboardData()).system_status;
}

export async function getPredictionDistribution(): Promise<PieSlice[]> {
  return (await getDashboardData()).prediction_distribution;
}

export async function getMonthlyPredictions(): Promise<LinePoint[]> {
  return (await getDashboardData()).monthly_trends;
}

export async function getRiskDistribution(): Promise<BarSlice[]> {
  return (await getDashboardData()).risk_distribution;
}

export async function getReportsAreaData(): Promise<AreaData[]> {
  return (await getDashboardData()).reports_area;
}

export async function getActivityTimeline(): Promise<ActivityEvent[]> {
  return (await getDashboardData()).activity;
}

export async function getDashboardSummary(): Promise<DashboardPayload["summary"]> {
  return (await getDashboardData()).summary;
}

export function invalidateDashboardCache() {
  dashboardCache = null;
}
