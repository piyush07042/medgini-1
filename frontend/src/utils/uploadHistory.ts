import type { UploadHistoryItem, UploadReportResponse, WorkflowState } from "../types/api";

const STORAGE_KEY = "medigenie_upload_history";
const MAX_HISTORY_ITEMS = 8;

function readStoredHistory(): UploadHistoryItem[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as UploadHistoryItem[]) : [];
  } catch {
    return [];
  }
}

function writeStoredHistory(history: UploadHistoryItem[]) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

function inferFileType(fileName: string) {
  const extension = fileName.split(".").pop()?.toLowerCase();
  if (extension === "pdf") {
    return "PDF";
  }
  if (extension === "png" || extension === "jpg" || extension === "jpeg") {
    return "Image";
  }
  return "File";
}

function deriveSummary(workflowState?: WorkflowState) {
  const notes = workflowState?.metadata?.processing_notes as string[] | undefined;
  if (notes?.length) {
    return notes[0];
  }

  const reportText = workflowState?.report_text;
  if (typeof reportText === "string" && reportText.trim()) {
    return reportText.trim().slice(0, 120);
  }

  return "Report processed successfully.";
}

function deriveRiskLevel(workflowState?: WorkflowState) {
  const diseaseRisk = workflowState?.disease_risk as Record<string, any> | undefined;
  return diseaseRisk?.risk_level || diseaseRisk?.overall_risk || diseaseRisk?.label || undefined;
}

function deriveConfidence(workflowState?: WorkflowState) {
  const diseaseRisk = workflowState?.disease_risk as Record<string, any> | undefined;
  const value = diseaseRisk?.confidence;
  return typeof value === "number" ? value : undefined;
}

function derivePrediction(workflowState?: WorkflowState) {
  const diseaseRisk = workflowState?.disease_risk as Record<string, any> | undefined;
  return diseaseRisk?.prediction || diseaseRisk?.disease || undefined;
}

export function loadUploadHistory(): UploadHistoryItem[] {
  return readStoredHistory();
}

export function saveUploadHistoryEntry(file: File, result: UploadReportResponse) {
  const workflowState = result.workflow_state;
  const patientContext = workflowState?.patient as Record<string, any> | undefined;
  const patientName = [patientContext?.first_name, patientContext?.last_name]
    .filter(Boolean)
    .join(" ")
    .trim();

  const item: UploadHistoryItem = {
    id: `${Date.now()}-${file.name}`,
    filename: file.name,
    fileType: inferFileType(file.name),
    uploadedAt: new Date().toISOString(),
    status: workflowState ? "completed" : "failed",
    patientName: patientName || undefined,
    prediction: derivePrediction(workflowState),
    riskLevel: deriveRiskLevel(workflowState),
    confidence: deriveConfidence(workflowState),
    summary: deriveSummary(workflowState),
    workflowState,
  };

  const history = [item, ...readStoredHistory()].slice(0, MAX_HISTORY_ITEMS);
  writeStoredHistory(history);
  return history;
}

export function clearUploadHistory() {
  writeStoredHistory([]);
  return [];
}
