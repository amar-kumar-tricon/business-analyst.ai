/**
 * Projects API — mirrors `/api/projects/*` endpoints from the FastAPI server.
 */
import {http} from './http';

export const projectsApi = {
    /** Create a new project with name + optional context text */
    create: (name: string, additional_context = '') =>
        http.post('/projects', {name, additional_context}).then((r) => r.data),

    /** Get full project state */
    get: (id: string) => http.get(`/projects/${id}`).then((r) => r.data),

    /** Upload a single file to the project */
    uploadFile: (id: string, file: File) => {
        const form = new FormData();
        form.append('file', file);
        return http
            .post(`/projects/${id}/files`, form, {
                headers: {'Content-Type': 'multipart/form-data'},
            })
            .then((r) => r.data);
    },

    /** Run Stage 1 (Analyser) + Stage 2 (Discovery first question) */
    run: (id: string) => http.post(`/projects/${id}/run`).then((r) => r.data),

    /** Answer a discovery question */
    answerDiscovery: (
        id: string,
        answer: string | null,
        status: 'answered' | 'deferred' | 'na' = 'answered',
        selectedOptionIndex: number | null = null,
        terminate = false,
    ) =>
        http
            .post(`/projects/${id}/discovery/answer`, {
                answer,
                status,
                selected_option_index: selectedOptionIndex,
                terminate,
            })
            .then((r) => r.data),

    /** Run Stage 3 (Architecture) */
    runArchitecture: (id: string) =>
        http.post(`/projects/${id}/architecture`).then((r) => r.data),

    /** Approve and export final artifacts */
    approve: (id: string, userEditsPayload: object | null = null) =>
        http
            .post(`/projects/${id}/approve`, {
                user_edits_payload: userEditsPayload,
            })
            .then((r) => r.data),
};
