import axios from "axios";
import api from "./client";
import { ApiResponse, Patient, PatientTimelineEvent, PatientVisitRecord } from "../types/api";

export type CreatePatientPayload = {
  first_name: string;
  last_name: string;
  age: number;
  gender: string;
  medical_history?: Record<string, any>;
  allergies?: string[];
  current_medications?: string[];
};

export type UpdatePatientPayload = Partial<CreatePatientPayload>;

export type PatientListQuery = {
  search?: string;
  gender?: string;
  sort_by?: string;
  sort_dir?: string;
  page?: number;
  page_size?: number;
};

export const listPatients = async (query: PatientListQuery = {}): Promise<ApiResponse<Patient[]>> => {
  const response = await api.get<ApiResponse<any>>("/patients/", {
    params: {
      search: query.search ?? "",
      gender: query.gender ?? "all",
      sort_by: query.sort_by ?? "created_at",
      sort_dir: query.sort_dir ?? "desc",
      page: query.page ?? 1,
      page_size: query.page_size ?? 8,
    },
  });

  const payload = response.data.data;
  const items = Array.isArray(payload) ? payload : payload?.items ?? [];

  return {
    ...response.data,
    data: items as Patient[],
  };
};

export const createPatient = async (payload: CreatePatientPayload): Promise<ApiResponse<Patient>> => {
  const response = await api.post<ApiResponse<Patient>>("/patients/", payload);
  return response.data;
};

export const getPatientDetails = async (patientId: number): Promise<Patient | null> => {
  try {
    const response = await api.get<ApiResponse<Patient>>(`/patients/${patientId}`);
    return response.data.data;
  } catch (error) {
    if (axios.isAxiosError(error) && [404, 405].includes(error.response?.status ?? 0)) {
      const list = await listPatients();
      return list.data?.find((patient) => patient.id === patientId) ?? null;
    }
    throw error;
  }
};

export const updatePatient = async (
  patientId: number,
  payload: UpdatePatientPayload
): Promise<ApiResponse<Patient>> => {
  const response = await api.put<ApiResponse<Patient>>(`/patients/${patientId}`, payload);
  return response.data;
};

export const deletePatient = async (patientId: number): Promise<ApiResponse<null>> => {
  const response = await api.delete<ApiResponse<null>>(`/patients/${patientId}`);
  return response.data;
};

export const uploadPatientAvatar = async (patientId: number, file: File): Promise<ApiResponse<Patient>> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<ApiResponse<Patient>>(`/patients/${patientId}/avatar`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

export const getPatientTimeline = async (patientId: number): Promise<ApiResponse<PatientTimelineEvent[]>> => {
  const response = await api.get<ApiResponse<PatientTimelineEvent[]>>(`/patients/${patientId}/timeline`);
  return response.data;
};

export const getPatientVisits = async (patientId: number): Promise<ApiResponse<PatientVisitRecord[]>> => {
  const response = await api.get<ApiResponse<PatientVisitRecord[]>>(`/patients/${patientId}/visits`);
  return response.data;
};
