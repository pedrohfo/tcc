// src/utils/api.ts
import axios from "axios";

const API_BASE = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
});

function setAuthHeader(token: string | null) {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
}

export function bootstrapAuthFromStorage() {
  if (typeof window === "undefined") return;
  const access = localStorage.getItem("access");
  setAuthHeader(access);
}

export function saveTokens(access: string, refresh: string) {
  localStorage.setItem("access", access);
  localStorage.setItem("refresh", refresh);
  setAuthHeader(access);
}

export function clearTokens() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  setAuthHeader(null);
}

api.interceptors.request.use((config) => {
  const access = typeof window !== "undefined" ? localStorage.getItem("access") : null;
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as any;

    // Tenta refresh quando 401 e ainda não tentou
    if (error?.response?.status === 401 && !original?._retry) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem("refresh");
        if (!refresh) {
          clearTokens();
          if (typeof window !== "undefined") window.location.href = "/";
          return Promise.reject(error);
        }
        const r = await axios.post(`${API_BASE}/auth/refresh/`, { refresh });
        const newAccess = r.data?.access;
        if (newAccess) {
          localStorage.setItem("access", newAccess);
          setAuthHeader(newAccess);
          original.headers = { ...(original.headers || {}), Authorization: `Bearer ${newAccess}` };
          return api(original);
        }
      } catch {
        clearTokens();
        if (typeof window !== "undefined") window.location.href = "/";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
