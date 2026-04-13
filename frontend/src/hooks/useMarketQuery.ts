import { useQuery } from '@tanstack/react-query'
import { marketApi } from '@/lib/api'

export function useMarketTicker() {
  return useQuery({
    queryKey: ['market', 'ticker'],
    queryFn: async () => {
      const { data } = await marketApi.ticker()
      return data
    },
    refetchInterval: 60000, // Refresh every 60s
    staleTime: 30000,
  })
}

export function useCompanyOverview(symbol: string) {
  return useQuery({
    queryKey: ['market', 'company', symbol],
    queryFn: async () => {
      const { data } = await marketApi.company(symbol)
      return data
    },
    enabled: !!symbol,
    staleTime: 60000,
  })
}

export function useRiskDashboard() {
  return useQuery({
    queryKey: ['market', 'risk'],
    queryFn: async () => {
      const { data } = await marketApi.riskDashboard()
      return data
    },
    refetchInterval: 300000, // Refresh every 5 min
    staleTime: 120000,
  })
}

export function useBrandIntel() {
  return useQuery({
    queryKey: ['market', 'brand'],
    queryFn: async () => {
      const { data } = await marketApi.brandIntel()
      return data
    },
    refetchInterval: 300000,
    staleTime: 120000,
  })
}
