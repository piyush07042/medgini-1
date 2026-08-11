import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Track whether a token refresh is already in flight to prevent duplicate refresh calls
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use((config) => {
  const rawAuth = localStorage.getItem("medigenie_auth");
  if (rawAuth && config.headers) {
    try {
      const auth = JSON.parse(rawAuth) as { token?: string };
      if (auth.token) {
        config.headers.Authorization = `Bearer ${auth.token}`;
      }
    } catch {
      // ignore invalid storage state
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If we get a 401 and this request hasn't already been retried
    if (error?.response?.status === 401 && !originalRequest._retry) {
      // Skip refresh for auth endpoints themselves to avoid infinite loops
      if (originalRequest.url?.includes("/auth/refresh") || originalRequest.url?.includes("/auth/login")) {
        localStorage.removeItem("medigenie_auth");
        if (window.location.pathname !== "/login") {
          window.location.assign("/login");
        }
        return Promise.reject(error);
      }

      // If a refresh is already in flight, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const rawAuth = localStorage.getItem("medigenie_auth");
        if (!rawAuth) throw new Error("No auth data");

        const auth = JSON.parse(rawAuth) as { token?: string; refresh_token?: string; user?: unknown };
        if (!auth.refresh_token) throw new Error("No refresh token");

        // Call the refresh endpoint
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: auth.refresh_token,
        });

        const newAccessToken = response.data?.data?.access_token ?? response.data?.access_token;
        const newRefreshToken = response.data?.data?.refresh_token ?? response.data?.refresh_token ?? auth.refresh_token;
        const newUser = response.data?.data?.user ?? auth.user;

        if (!newAccessToken) throw new Error("No access token in refresh response");

        // Persist updated tokens
        localStorage.setItem(
          "medigenie_auth",
          JSON.stringify({ token: newAccessToken, refresh_token: newRefreshToken, user: newUser })
        );
        api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);

        // Retry the original request with the new token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem("medigenie_auth");
        if (window.location.pathname !== "/login") {
          window.location.assign("/login");
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
