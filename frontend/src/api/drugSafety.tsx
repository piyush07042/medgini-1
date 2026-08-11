import api from "./client";
import { ApiResponse } from "../types/api";

export type DrugSafetyPayload = {
  medications: string[];
  allergies?: string[];
};

export type DrugSafetyAssessment = {
  id: number;
  created_at: string;
  assessment: Record<string, any>;
};

export type DrugSafetyStoreResponse = {
  id: number;
  status: Record<string, any>;
};

export const analyzeDrugSafety = async (payload: DrugSafetyPayload): Promise<ApiResponse<Record<string, any>>> => {
  const response = await api.post<ApiResponse<Record<string, any>>>("/drug-safety/analyze", payload);
  return response.data;
};

export const storeDrugSafetyAssessment = async (
  payload: DrugSafetyPayload & { patient_id?: number }
): Promise<ApiResponse<DrugSafetyStoreResponse>> => {
  const response = await api.post<ApiResponse<DrugSafetyStoreResponse>>("/drug-safety/store", payload);
  return response.data;
};

export const getDrugSafetyForPatient = async (patientId: number): Promise<ApiResponse<DrugSafetyAssessment[]>> => {
  const response = await api.get<ApiResponse<DrugSafetyAssessment[]>>(`/drug-safety/patient/${patientId}`);
  return response.data;
};
