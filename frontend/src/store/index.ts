import { create } from 'zustand';
import { Case, Recommendation, PlannerExecution } from '@/types';

interface AppStore {
  selectedCase: Case | null;
  setSelectedCase: (case_: Case | null) => void;
  selectedRecommendation: Recommendation | null;
  setSelectedRecommendation: (rec: Recommendation | null) => void;
  selectedExecution: PlannerExecution | null;
  setSelectedExecution: (exec: PlannerExecution | null) => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  selectedCase: null,
  setSelectedCase: (case_) => set({ selectedCase: case_ }),
  selectedRecommendation: null,
  setSelectedRecommendation: (rec) => set({ selectedRecommendation: rec }),
  selectedExecution: null,
  setSelectedExecution: (exec) => set({ selectedExecution: exec }),
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
}));
