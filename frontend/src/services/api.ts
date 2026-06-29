import apiClient from '@/lib/api';
import { Case, Recommendation, PlannerExecution, Memory, Agent, Tool } from '@/types';

export const casesApi = {
  getAll: (params?: { page?: number; page_size?: number; status?: string; priority?: string; case_type?: string }) =>
    apiClient.get<any>('/cases', { params }),
  getById: (id: string) => apiClient.get<Case>(`/cases/${id}`),
  create: (data: Partial<Case>) => apiClient.post<Case>('/cases', data),
  update: (id: string, data: Partial<Case>) => apiClient.patch<Case>(`/cases/${id}`, data),
  delete: (id: string) => apiClient.delete(`/cases/${id}`),
};

export const recommendationsApi = {
  getAll: (caseId?: string) => apiClient.get<Recommendation[]>('/recommendations', { params: { case_id: caseId } }),
  getById: (id: string) => apiClient.get<Recommendation>(`/recommendations/${id}`),
  create: (data: Partial<Recommendation>) => apiClient.post<Recommendation>('/recommendations', data),
  update: (id: string, data: Partial<Recommendation>) => apiClient.patch<Recommendation>(`/recommendations/${id}`, data),
};

export const plannerApi = {
  execute: (data: { case_id: string; workflow_type: string }) => apiClient.post<PlannerExecution>('/planner/execute', data),
  getExecution: (id: string) => apiClient.get<PlannerExecution>(`/planner/executions/${id}`),
  listExecutions: (params?: { case_id?: string; limit?: number }) => apiClient.get<any>('/planner/executions', { params }),
  plan: (data: { case_id: string; workflow_type: string }) => apiClient.post<any>('/planner/plan', data),
};

export const memoryApi = {
  getAll: (params?: { memory_type?: string; case_id?: string }) => apiClient.get<Memory[]>('/memory', { params }),
  create: (data: Partial<Memory>) => apiClient.post<Memory>('/memory', data),
  delete: (id: string) => apiClient.delete(`/memory/${id}`),
  reindex: (id: string) => apiClient.post(`/memory/${id}/reindex`),
  getStats: () => apiClient.get<any>('/memory/stats'),
};

export const agentsApi = {
  getAll: () => apiClient.get<Agent[]>('/agents'),
  getById: (id: string) => apiClient.get<Agent>(`/agents/${id}`),
  discover: (capabilities?: string[]) => apiClient.get<Agent[]>('/agents/discover', { params: { capabilities } }),
  getStats: () => apiClient.get<any>('/agents/stats'),
};

export const toolsApi = {
  getAll: () => apiClient.get<Tool[]>('/tools'),
  getById: (id: string) => apiClient.get<Tool>(`/tools/${id}`),
  discover: (toolType?: string) => apiClient.get<Tool[]>('/tools/discover', { params: { tool_type: toolType } }),
  getStats: () => apiClient.get<any>('/tools/stats'),
};

export const feedbackApi = {
  create: (data: any) => {
    const recommendationId = data.recommendation_id || data.recommendationId;
    const decision = (data.decision || data.feedback_type || 'approved').toLowerCase();
    const normalizedDecision = decision === 'approval' ? 'approved' : decision === 'rejection' ? 'rejected' : decision;
    return apiClient.post(`/review/recommendations/${recommendationId}/review`, {
      decision: normalizedDecision,
      comments: data.comments || data.content || '',
      modified_content: data.modified_content || data.modifications,
      reviewer_id: data.reviewer_id || 'current-user'
    });
  }
};

export const documentsApi = {
  list: (caseId: string) => apiClient.get(`/documents/cases/${caseId}/documents`),
  upload: (caseId: string, formData: FormData, onProgress?: (pct: number) => void) =>
    apiClient.post(`/documents/cases/${caseId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (evt.total && onProgress) {
          onProgress(Math.round((evt.loaded * 100) / evt.total));
        }
      },
    }),
  delete: (docId: string) => apiClient.delete(`/documents/${docId}`),
  download: (docId: string) => `/api/v1/documents/${docId}/download`,
};

export const searchApi = {
  search: (q: string) => apiClient.get<any>('/search', { params: { q } }),
};

export const settingsApi = {
  get: () => apiClient.get<any>('/settings'),
  update: (data: any) => apiClient.put('/settings', data),
  testConnection: () => apiClient.post<any>('/settings/test-connection'),
};
