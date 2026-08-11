import api from "./client";
import type { ApiResponse } from "../types/api";
import type {
  ActivityEvent,
  AreaData,
  BarSlice,
  DashboardStat,
  LinePoint,
  PieSlice,
  RecentPatient,
  RecentPrediction,
  RecentReport,
  SystemStatusItem,
} from "../services/dashboardService";

export type DashboardSummary = {
  pending_reports: number;
  high_risk_patients: number;
  text: string;
};

export type DashboardPayload = {
  stats: DashboardStat[];
  recent_patients: RecentPatient[];
  recent_reports: RecentReport[];
  recent_predictions: RecentPrediction[];
  system_status: SystemStatusItem[];
  activity: ActivityEvent[];
  prediction_distribution: PieSlice[];
  monthly_trends: LinePoint[];
  risk_distribution: BarSlice[];
  reports_area: AreaData[];
  summary: DashboardSummary;
};

export async function fetchDashboard(): Promise<DashboardPayload> {
  const response = await api.get<ApiResponse<DashboardPayload>>("/dashboard");
  return response.data.data ?? {
    stats: [],
    recent_patients: [],
    recent_reports: [],
    recent_predictions: [],
    system_status: [],
    activity: [],
    prediction_distribution: [],
    monthly_trends: [],
    risk_distribution: [],
    reports_area: [],
    summary: {
      pending_reports: 0,
      high_risk_patients: 0,
      text: "No dashboard data available yet.",
    },
  };
}

export async function saveDashboardPrediction(
  payload: {
    patient_id: number;
    risk_assessment: Record<string, any>;
    rag_evidence?: Array<Record<string, any>>;
    drug_safety_alerts?: Record<string, any>;
    clinical_summary?: string;
    clinical_intelligence?: Record<string, any>;
  }
): Promise<void> {
  await api.post<ApiResponse<{ id: number }>>("/dashboard/prediction", payload);
}
