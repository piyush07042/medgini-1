import api from "./client";
import { ApiResponse } from "../types/api";

export type ChatPayload = {
  patient_context?: Record<string, any>;
  message: string;
  symptoms?: string[];
  medications?: string[];
  allergies?: string[];
  report_text?: string;
};

export type ChatResponseData = {
  reply: string;
  workflow_state?: Record<string, any> | null;
  agent_results?: Array<Record<string, any>> | null;
  metrics?: Record<string, any> | null;
  clinical_summary?: string | null;
};

export const sendChat = async (payload: ChatPayload): Promise<ApiResponse<ChatResponseData>> => {
  const response = await api.post<ApiResponse<ChatResponseData>>("/chat/", payload);
  return response.data;
};

export const storeConversation = async (payload: { patient_id?: number; title?: string; messages: Array<{ role: string; text: string; timestamp?: string; metadata?: Record<string, any> }>; metadata?: Record<string, any> }) => {
  const response = await api.post<ApiResponse<Record<string, any>>>("/chat/store", payload);
  return response.data;
};

export const getConversationsForPatient = async (patientId: number) => {
  const response = await api.get<ApiResponse<any[]>>(`/chat/patient/${patientId}/conversations`);
  return response.data;
};
