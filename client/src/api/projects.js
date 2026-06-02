/**
 * Projects API — mirrors `/api/projects/*` endpoints from the FastAPI server.
 * Keep function names aligned 1:1 with backend routes for easy navigation.
 */
import { http } from "./http";
const apiBase = (import.meta.env.VITE_API_BASE_URL ?? "/api").replace(/\/$/, "");
export const projectsApi = {
    create: (name, additional_context = "") => http
        .post("/projects", { name, additional_context })
        .then((r) => r.data),
    uploadFile: (id, file) => {
        const form = new FormData();
        form.append("file", file);
        return http
            .post(`/projects/${id}/files`, form, {
            headers: { "Content-Type": "multipart/form-data" },
        })
            .then((r) => r.data);
    },
    run: (id) => http.post(`/projects/${id}/run`).then((r) => r.data),
    answer: (id, args) => http
        .post(`/projects/${id}/discovery/answer`, args)
        .then((r) => r.data),
    approve: (id, user_edits_payload = null) => http
        .post(`/projects/${id}/approve`, { user_edits_payload })
        .then((r) => r.data),
    sprint: (id) => http
        .post(`/projects/${id}/sprint`)
        .then((r) => r.data),
    artifactUrl: (id, kind) => `${apiBase}/projects/${id}/artifacts/${kind}`,
    events: (id) => http
        .get(`/projects/${id}/events`)
        .then((r) => r.data),
};
