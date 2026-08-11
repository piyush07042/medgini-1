import { create } from "zustand";
import api from "../api/client";
import { login, logoutClientSession, refreshAuth, type AuthSession } from "../services/authService";
import type { User } from "../types/api";

type AuthState = {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: { email: string; password: string; rememberMe?: boolean }) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  initialize: () => Promise<void>;
};

const persistAuth = (token: string | null, refreshToken: string | null, user: User | null) => {
  if (token && user) {
    localStorage.setItem("medigenie_auth", JSON.stringify({ token, refresh_token: refreshToken, user }));
  } else {
    localStorage.removeItem("medigenie_auth");
  }
};

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  setUser: (user) => {
    set({ user, isAuthenticated: Boolean(user) });
    persistAuth(get().token, get().refreshToken, user);
  },
  setToken: (token) => {
    set({ token, isAuthenticated: Boolean(token) });
    persistAuth(token, get().refreshToken, get().user);
  },
  login: async (payload) => {
    set({ isLoading: true });
    try {
      const session: AuthSession = await login(payload);
      set({
        user: session.user,
        token: session.access_token,
        refreshToken: session.refresh_token ?? null,
        isAuthenticated: true,
        isLoading: false,
      });
      persistAuth(session.access_token, session.refresh_token ?? null, session.user);
      api.defaults.headers.common.Authorization = `Bearer ${session.access_token}`;
    } catch (error) {
      set({ isLoading: false, isAuthenticated: false });
      throw error;
    }
  },
  logout: async () => {
    set({ user: null, token: null, refreshToken: null, isAuthenticated: false, isLoading: false });
    logoutClientSession();
    delete api.defaults.headers.common.Authorization;
  },
  initialize: async () => {
    set({ isLoading: true });
    const snapshot = await refreshAuth();
    if (snapshot.token && snapshot.user) {
      set({
        token: snapshot.token,
        refreshToken: snapshot.refresh_token ?? null,
        user: snapshot.user,
        isAuthenticated: true,
        isLoading: false,
      });
      api.defaults.headers.common.Authorization = `Bearer ${snapshot.token}`;
      persistAuth(snapshot.token, snapshot.refresh_token ?? null, snapshot.user);
    } else {
      set({ token: null, refreshToken: null, user: null, isAuthenticated: false, isLoading: false });
      logoutClientSession();
      delete api.defaults.headers.common.Authorization;
    }
  },
}));
