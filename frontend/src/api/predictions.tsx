import api from "./client";
import {
  ApiResponse,
  BreastCancerPredictionResponse,
  DiabetesPredictionResponse,
  HepatitisPredictionResponse,
  HeartDiseasePredictionResponse,
  HeartFailurePredictionResponse,
  KidneyDiseasePredictionResponse,
  LiverDiseasePredictionResponse,
  ParkinsonsPredictionResponse,
  StrokePredictionResponse,
  HeartDiseasePredictionRequest,
  DiabetesPredictionRequest,
  KidneyDiseasePredictionRequest,
  LiverDiseasePredictionRequest,
  BreastCancerPredictionRequest,
  ParkinsonsPredictionRequest,
  HepatitisPredictionRequest,
  HeartFailurePredictionRequest,
  StrokePredictionRequest,
} from "../types/api";

export const predictHeartDisease = async (
  payload: HeartDiseasePredictionRequest,
): Promise<HeartDiseasePredictionResponse> => {
  const response = await api.post<HeartDiseasePredictionResponse>("/heart-disease/predict", payload);
  return response.data;
};

export const predictDiabetes = async (
  payload: DiabetesPredictionRequest,
): Promise<DiabetesPredictionResponse> => {
  const response = await api.post<DiabetesPredictionResponse>("/diabetes/predict", payload);
  return response.data;
};

export const predictKidneyDisease = async (
  payload: KidneyDiseasePredictionRequest,
): Promise<KidneyDiseasePredictionResponse> => {
  const response = await api.post<KidneyDiseasePredictionResponse>("/kidney-disease/predict", payload);
  return response.data;
};

export const predictLiverDisease = async (
  payload: LiverDiseasePredictionRequest,
): Promise<LiverDiseasePredictionResponse> => {
  const response = await api.post<LiverDiseasePredictionResponse>("/liver/predict", payload);
  return response.data;
};

export const predictBreastCancer = async (
  payload: BreastCancerPredictionRequest,
): Promise<BreastCancerPredictionResponse> => {
  const response = await api.post<BreastCancerPredictionResponse>("/breast-cancer/predict", payload);
  return response.data;
};

export const predictParkinsons = async (
  payload: ParkinsonsPredictionRequest,
): Promise<ParkinsonsPredictionResponse> => {
  const response = await api.post<ParkinsonsPredictionResponse>("/parkinsons/predict", payload);
  return response.data;
};

export const predictHepatitis = async (
  payload: HepatitisPredictionRequest,
): Promise<HepatitisPredictionResponse> => {
  const response = await api.post<HepatitisPredictionResponse>("/hepatitis/predict", payload);
  return response.data;
};

export const predictHeartFailure = async (
  payload: HeartFailurePredictionRequest,
): Promise<HeartFailurePredictionResponse> => {
  const response = await api.post<HeartFailurePredictionResponse>("/heart-failure/predict", payload);
  return response.data;
};

export const predictStroke = async (
  payload: StrokePredictionRequest,
): Promise<StrokePredictionResponse> => {
  const response = await api.post<StrokePredictionResponse>("/stroke/predict", payload);
  return response.data;
};
