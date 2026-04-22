/**
 * Projects API — mirrors `/api/projects/*` endpoints from the FastAPI server.
 * Keep function names aligned 1:1 with backend routes for easy navigation.
 */
import { http } from "./http";
import type { Project, StageName } from "../types";

export const projectsApi = {
  create: (name: string) => http.post<Project>("/projects", { name }).then((r) => r.data),
  get: (id: string) => http.get<Project>(`/projects/${id}`).then((r) => r.data),

  uploadDocuments: (id: string, files: File[], additionalContext = "") => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("additional_context", additionalContext);
    return http.post(`/projects/${id}/documents`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  triggerAnalyse: (id: string) => http.post(`/projects/${id}/analyse`),
  approveStage: (id: string, stage: StageName, edits?: unknown) =>
    http.post(`/projects/${id}/approve/${stage}`, { edits }),

  getDiscovery: (id: string) => http.get(`/projects/${id}/discovery`).then((r) => r.data),
  answerDiscovery: (id: string, answer: string, status = "answered") =>
    http.post(`/projects/${id}/discovery/answer`, { answer, status }),

  getArchitecture: (id: string) => http.get(`/projects/${id}/architecture`).then((r) => r.data),
  regenerateArchitecture: (id: string) => http.post(`/projects/${id}/architecture/regenerate`),

  getSprint: (id: string) => http.get(`/projects/${id}/sprint`).then((r) => r.data),
  finalize: (id: string) => http.post(`/projects/${id}/finalize`),
  listVersions: (id: string) => http.get(`/projects/${id}/versions`).then((r) => r.data),

  export: (id: string, stage: StageName, format: "pdf" | "docx") =>
    http.post(`/projects/${id}/export`, { stage, format }, { responseType: "blob" }),
};
