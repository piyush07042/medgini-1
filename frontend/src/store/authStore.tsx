import { create } from "zustand";
import { User } from "../types/api";

type AuthState = {
  user: User | null;
  token: string | null;
  setUser: (user: User) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem("medigenie_token"),
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) {
      localStorage.setItem("medigenie_token", token);
    } else {
      localStorage.removeItem("medigenie_token");
    }
    set({ token });
  },
  logout: () => {
    localStorage.removeItem("medigenie_token");
    set({ user: null, token: null });
  },
}));
