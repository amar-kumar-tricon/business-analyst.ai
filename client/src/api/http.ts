/**
 * Axios instance shared by all API modules.
 * Base URL is driven by VITE_API_BASE_URL (defaults to "/api" via Vite proxy).
 */
import axios from "axios";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  timeout: 60_000,
});

http.interceptors.response.use(
  (r) => r,
  (err) => {
    // TODO: wire toast notifications / global error handler here.
    console.error("API error:", err?.response?.data ?? err.message);
    return Promise.reject(err);
  }
);
