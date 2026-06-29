import apiClient from '@/lib/api';

export const workflowApi = {
  execute: (data: { case_id: string; workflow_type?: string; documents?: any[] }) => 
    apiClient.post<{ execution_id: string; stream_url: string }>('/workflow/execute', data),
  
  getStatus: (executionId: string) => 
    apiClient.get<{ status: string; progress: number; total_steps: number }>(`/workflow/status/${executionId}`),
  
  submitFeedback: (recommendationId: string, feedback: { action: string; rating?: number; comments?: string }) =>
    apiClient.post(`/workflow/feedback/${recommendationId}`, feedback),
};
