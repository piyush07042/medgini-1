import api from "./client";
import { ApiResponse } from "../types/api";

export const getProfile = async () => {
  const response = await api.get<ApiResponse<any>>("/settings/profile");
  return response.data;
};

export const updateProfile = async (payload: { email?: string; full_name?: string }) => {
  const response = await api.put<ApiResponse<any>>("/settings/profile", payload);
  return response.data;
};

export const changePassword = async (payload: { current_password: string; new_password: string }) => {
  const response = await api.post<ApiResponse<any>>("/settings/change-password", payload);
  return response.data;
};

export const uploadAvatar = async (file: File) => {
  const form = new FormData();
  form.append("file", file);
  const response = await api.post<ApiResponse<any>>("/settings/avatar", form, { headers: { "Content-Type": "multipart/form-data" } });
  return response.data;
};

export const getLoginHistory = async () => {
  const response = await api.get<ApiResponse<any[]>>("/settings/login-history");
  return response.data;
};

export const listSessions = async () => {
  const response = await api.get<ApiResponse<any[]>>("/settings/sessions");
  return response.data;
};

export const revokeSession = async (id: number) => {
  const response = await api.post<ApiResponse<any>>(`/settings/sessions/${id}/revoke`);
  return response.data;
};

export const listDevices = async () => {
  const response = await api.get<ApiResponse<any[]>>("/settings/devices");
  return response.data;
};
