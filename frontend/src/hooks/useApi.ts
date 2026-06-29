import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { casesApi, recommendationsApi, plannerApi, memoryApi, agentsApi, toolsApi, feedbackApi, searchApi, settingsApi } from '@/services/api';

// ─── Cases ────────────────────────────────────────────────────

export const useCases = (params?: { page?: number; page_size?: number; status?: string; priority?: string; case_type?: string }) =>
  useQuery({
    queryKey: ['cases', params],
    queryFn: async () => {
      const response = await casesApi.getAll(params);
      return (response.data as any)?.items || response.data || [];
    }
  });

export const useCasesWithPagination = (params?: { page?: number; page_size?: number; status?: string; priority?: string; case_type?: string }) =>
  useQuery({
    queryKey: ['cases', 'paginated', params],
    queryFn: async () => {
      const response = await casesApi.getAll(params);
      const data = response.data as any;
      return {
        items: data?.items || data || [],
        total: data?.total || 0,
        page: data?.page || 1,
        page_size: data?.page_size || 20,
        total_pages: data?.total_pages || 1,
      };
    }
  });

export const useCase = (id: string) =>
  useQuery({ queryKey: ['case', id], queryFn: () => casesApi.getById(id).then(r => r.data), enabled: !!id });

export const useCreateCase = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: casesApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cases'] }),
  });
};

export const useUpdateCase = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => casesApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['cases'] });
      queryClient.invalidateQueries({ queryKey: ['case', variables.id] });
    },
  });
};

export const useDeleteCase = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => casesApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cases'] }),
  });
};

// ─── Recommendations ─────────────────────────────────────────

export const useRecommendations = (caseId?: string) =>
  useQuery({
    queryKey: ['recommendations', caseId],
    queryFn: async () => {
      const response = await recommendationsApi.getAll(caseId);
      return (response.data as any)?.items || response.data || [];
    }
  });

export const useRecommendation = (id: string) =>
  useQuery({ queryKey: ['recommendation', id], queryFn: () => recommendationsApi.getById(id).then(r => r.data), enabled: !!id });

export const useUpdateRecommendation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => recommendationsApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recommendations'] }),
  });
};

// ─── Planner ─────────────────────────────────────────────────

export const usePlannerExecution = (id: string) =>
  useQuery({ queryKey: ['execution', id], queryFn: () => plannerApi.getExecution(id).then(r => r.data), enabled: !!id });

export const usePlannerExecutions = (params?: { case_id?: string; limit?: number }) =>
  useQuery({
    queryKey: ['executions', params],
    queryFn: async () => {
      const response = await plannerApi.listExecutions(params);
      return (response.data as any)?.executions || [];
    }
  });

export const useExecutePlanner = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: plannerApi.execute,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['executions'] }),
  });
};

// ─── Memory ──────────────────────────────────────────────────

export const useMemories = (params?: { memory_type?: string; case_id?: string }) =>
  useQuery({
    queryKey: ['memories', params],
    queryFn: async () => {
      const response = await memoryApi.getAll(params);
      return response.data || [];
    },
    retry: 1,
  });

export const useMemoryStats = () =>
  useQuery({
    queryKey: ['memory-stats'],
    queryFn: async () => {
      const response = await memoryApi.getStats();
      return response.data;
    },
  });

export const useDeleteMemory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => memoryApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] });
      queryClient.invalidateQueries({ queryKey: ['memory-stats'] });
    },
  });
};

export const useReindexMemory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => memoryApi.reindex(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['memories'] }),
  });
};

// ─── Agents ──────────────────────────────────────────────────

export const useAgents = () => useQuery({
  queryKey: ['agents'],
  queryFn: async () => {
    const response = await agentsApi.getAll();
    return (response.data as any)?.agents || (response.data as any)?.items || response.data || [];
  }
});

export const useTools = () => useQuery({
  queryKey: ['tools'],
  queryFn: async () => {
    const response = await toolsApi.getAll();
    return (response.data as any)?.items || response.data || [];
  }
});

// ─── Feedback ────────────────────────────────────────────────

export const useCreateFeedback = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: feedbackApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recommendations'] }),
  });
};

// ─── Search ──────────────────────────────────────────────────

export const useSearch = (query: string) =>
  useQuery({
    queryKey: ['search', query],
    queryFn: async () => {
      const response = await searchApi.search(query);
      return response.data;
    },
    enabled: query.length >= 2,
  });

// ─── Settings ────────────────────────────────────────────────

export const useSettings = () =>
  useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const response = await settingsApi.get();
      return response.data;
    },
  });

export const useUpdateSettings = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: settingsApi.update,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings'] }),
  });
};

export const useTestConnection = () =>
  useMutation({
    mutationFn: settingsApi.testConnection,
  });
