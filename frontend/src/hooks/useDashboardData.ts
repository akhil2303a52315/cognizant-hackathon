import { useQuery } from '@tanstack/react-query'
import { riskApi, healthApi, ragApi, ingestApi, modelsApi } from '@/lib/api'

export function useSuppliers() {
  return useQuery({
    queryKey: ['risk', 'suppliers'],
    queryFn: async () => {
      const { data } = await riskApi.suppliers()
      return data
    },
    staleTime: 60000,
  })
}

export function useRiskHeatmap() {
  return useQuery({
    queryKey: ['risk', 'heatmap'],
    queryFn: async () => {
      const { data } = await riskApi.heatmap()
      return data
    },
    staleTime: 120000,
  })
}

export function useSystemHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await healthApi.check()
      return data
    },
    refetchInterval: 30000,
    staleTime: 15000,
  })
}

export function useRAGStats() {
  return useQuery({
    queryKey: ['rag', 'stats'],
    queryFn: async () => {
      const { data } = await ragApi.stats()
      return data
    },
    staleTime: 120000,
  })
}

export function useIngestStatus() {
  return useQuery({
    queryKey: ['ingest', 'status'],
    queryFn: async () => {
      const { data } = await ingestApi.status()
      return data
    },
    refetchInterval: 60000,
    staleTime: 30000,
  })
}

export function useModelsStatus() {
  return useQuery({
    queryKey: ['models', 'status'],
    queryFn: async () => {
      const { data } = await modelsApi.list()
      return data
    },
    staleTime: 120000,
  })
}
