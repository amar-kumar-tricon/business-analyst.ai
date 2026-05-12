/**
 * Global app store (Zustand). Holds the active project id and run result.
 */
import {create} from 'zustand';

interface ProjectState {
    id: string;
    runResult?: any;
}

interface AppState {
    project: ProjectState | null;
    setProject: (p: ProjectState | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
    project: null,
    setProject: (project) => set({project}),
}));
