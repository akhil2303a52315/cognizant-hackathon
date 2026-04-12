import { useMutation, useQuery } from '@tanstack/react-query'
import { ragApi } from '@/lib/api'
import type { RAGResponse } from '@/types/rag'

export function useRAGQuery() {
  return useMutation({
    mutationFn: async ({ query, mode = 'standard', topK = 5 }: { query: string; mode?: 'standard' | 'graph' | 'hybrid'; topK?: number }) => {
      if (mode === 'graph') {
        const { data } = await ragApi.graphQuery(query)
        return data
      }
      if (mode === 'hybrid') {
        const { data } = await ragApi.hybridQuery(query, topK)
        return data
      }
      const { data } = await ragApi.query(query, topK)
      return data as RAGResponse
    },
  })
}

export function useRAGStats() {
  return useQuery({
    queryKey: ['rag-stats'],
    queryFn: async () => {
      const { data } = await ragApi.stats()
      return data
    },
    staleTime: 30000,
  })
}

export function useRAGCollections() {
  return useQuery({
    queryKey: ['rag-collections'],
    queryFn: async () => {
      const { data } = await ragApi.collections()
      return data
    },
    staleTime: 30000,
  })
}
