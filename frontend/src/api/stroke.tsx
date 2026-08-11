import api from "./client";
import { ApiResponse, StrokePredictionRequest, StrokePredictionResponse } from "../types/api";

export const predictStroke = async (payload: StrokePredictionRequest): Promise<StrokePredictionResponse> => {
  const response = await api.post<StrokePredictionResponse>("/stroke/predict", payload);
  return response.data;
};

export const strokeHealth = async (): Promise<StrokePredictionResponse> => {
  const response = await api.get<StrokePredictionResponse>("/stroke/health");
  return response.data;
};
