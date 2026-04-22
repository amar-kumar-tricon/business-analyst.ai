/**
 * Global app store (Zustand). Holds the active project id and cached stage outputs
 * so every page can read from a single source of truth.
 */
import { create } from "zustand";
import type { Project } from "../types";

interface AppState {
  project: Project | null;
  setProject: (p: Project | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  project: null,
  setProject: (project) => set({ project }),
}));
