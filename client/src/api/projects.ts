/**
 * Projects API — mirrors `/api/projects/*` endpoints from the FastAPI server.
 * Keep function names aligned 1:1 with backend routes for easy navigation.
 */
import {http} from './http';

import type {
    AnswerResponse,
    AnswerStatus,
    ApproveResponse,
    ArchitectureResponse,
    CreateProjectResponse,
    RunResponse,
    UploadFileResponse,
} from '../types';

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(
    /\/$/,
    '',
);

export const projectsApi = {
    create: (name: string, additional_context = '') =>
        http
            .post<CreateProjectResponse>('/projects', {
                name,
                additional_context,
            })
            .then((r) => r.data),

    uploadFile: (id: string, file: File) => {
        const form = new FormData();
        form.append('file', file);
        return http
            .post<UploadFileResponse>(`/projects/${id}/files`, form, {
                headers: {'Content-Type': 'multipart/form-data'},
            })
            .then((r) => r.data);
    },

    run: (id: string) =>
        http.post<RunResponse>(`/projects/${id}/run`).then((r) => r.data),

    answer: (
        id: string,
        args: {
            answer: string | null;
            status: AnswerStatus;
            selected_option_index: number | null;
            terminate: boolean;
        },
    ) =>
        http
            .post<AnswerResponse>(`/projects/${id}/discovery/answer`, args)
            .then((r) => r.data),

    approve: (
        id: string,
        user_edits_payload: Record<string, unknown> | null = null,
    ) =>
        http
            .post<ApproveResponse>(`/projects/${id}/approve`, {
                user_edits_payload,
            })
            .then((r) => r.data),

    runArchitecture: (id: string) =>
        http
            .post<ArchitectureResponse>(`/projects/${id}/architecture`)
            .then((r) => r.data),

    artifactUrl: (id: string, kind: 'md' | 'pdf' | 'docx') =>
        `${apiBase}/projects/${id}/artifacts/${kind}`,

    events: (id: string) =>
        http
            .get<{
                project_id: string;
                events: unknown[];
            }>(`/projects/${id}/events`)
            .then((r) => r.data),
};
