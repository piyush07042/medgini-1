import { useMemo } from "react";
import { useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getPatientDetails } from "../api/patients";
import type { Patient } from "../types/api";

export function usePredictionContext() {
  const location = useLocation();
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const queryPatientId = searchParams.has("patientId") ? Number(searchParams.get("patientId")) : undefined;
  const ocrState = location.state as { result?: { workflow_state?: Record<string, any> } } | null;
  const extractedMetrics = ocrState?.result?.workflow_state?.extracted_metrics;
  const patientContext = ocrState?.result?.workflow_state?.patient;
  const patientId = queryPatientId ?? (patientContext?.id ? Number(patientContext.id) : undefined);

  const patientQuery = useQuery({
    queryKey: ["predictionPatient", patientId],
    queryFn: () => (patientId ? getPatientDetails(patientId) : Promise.resolve(null)),
    enabled: Boolean(patientId),
    staleTime: 1000 * 60 * 5,
  });

  return {
    patientId,
    patient: patientQuery.data as Patient | null,
    patientLoading: patientQuery.isLoading,
    patientError: patientQuery.error,
    extractedMetrics,
    patientContext,
  };
}
