import api from "./client";
import { ApiResponse, User } from "../types/api";

export type RegisterPayload = {
  email: string;
  password: string;
  full_name: string;
  role?: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export const registerUser = async (payload: RegisterPayload): Promise<ApiResponse<User>> => {
  const response = await api.post<ApiResponse<User>>("/auth/register", payload);
  return response.data;
};

export const loginUser = async (payload: LoginPayload): Promise<LoginResponse> => {
  const form = new URLSearchParams();
  form.append("username", payload.email);
  form.append("password", payload.password);

  const response = await api.post<{
    access_token: string;
    token_type: string;
    success: boolean;
    message: string;
    data: { access_token: string; token_type: string; user: User };
  }>("/auth/login", form, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return {
    access_token: response.data.data.access_token,
    token_type: response.data.data.token_type,
    user: response.data.data.user,
  };
};
