/**
 * Axios instance shared by all API modules.
 * Base URL is driven by VITE_API_BASE_URL (defaults to "/api" via Vite proxy).
 *
 * Timeout is 10 minutes because Stage 1 + 2 issues several LLM calls
 * (analyse_node alone can take 100s+ on a multi-section BRD).
 */
import axios from "axios";
export const http = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
    timeout: 600_000,
});
http.interceptors.response.use((r) => r, (err) => {
    console.error("API error:", err?.response?.data ?? err.message);
    return Promise.reject(err);
});
