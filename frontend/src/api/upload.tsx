import axios from "axios";
import api from "./client";
import { ApiResponse, UploadReportResponse } from "../types/api";

export type UploadProgressCallback = (progress: number) => void;

export const uploadReport = async (
  file: File,
  patientContext?: Record<string, any>,
  onProgress?: UploadProgressCallback,
  signal?: AbortSignal
): Promise<ApiResponse<UploadReportResponse>> => {
  const formData = new FormData();
  formData.append("file", file);

  if (patientContext) {
    formData.append("patient_context_json", JSON.stringify(patientContext));
  }

  const response = await api.post<ApiResponse<UploadReportResponse>>("/upload/report", formData, {
    onUploadProgress: (event) => {
      if (!event.total) return;
      const percent = Math.round((event.loaded * 100) / event.total);
      onProgress?.(percent);
    },
    signal,
  });

  return response.data;
};
