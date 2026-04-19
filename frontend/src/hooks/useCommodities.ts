import { useQuery, useQueryClient } from '@tanstack/react-query'
import { marketApi } from '@/lib/api'

export interface CommodityData {
  name: string
  symbol: string
  icon: string
  category: string
  unit: string
  current_price: number
  change: number
  change_percent: number
  prev_close: number
  high: number
  low: number
  open: number
  timestamp: number
  data_freshness: string
  market_hours: boolean
  error?: string | null
  usd_price?: number
  usd_inr_rate?: number
  currency?: string
  currency_symbol?: string
}

export interface CommoditiesResponse {
  commodities: CommodityData[]
  timestamp: number
  count: number
  market_hours: boolean
}

export function useCommodities() {
  const queryClient = useQueryClient()

  const {
    data: commoditiesData,
    isLoading,
    error,
    refetch,
    dataUpdatedAt,
  } = useQuery<CommoditiesResponse>({
    queryKey: ['commodities'],
    queryFn: async () => {
      const response = await marketApi.commodityPrices()
      return response.data
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 3 * 60 * 1000, // 3 minutes auto-refresh
  })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['commodities'] })
    return refetch()
  }

  const getTimeSinceUpdate = () => {
    if (!dataUpdatedAt) return null
    const now = Date.now()
    const diff = now - dataUpdatedAt
    const minutes = Math.floor(diff / (1000 * 60))
    
    if (minutes < 1) return 'Just now'
    if (minutes === 1) return '1 min ago'
    return `${minutes} min ago`
  }

  const getDataFreshnessColor = (freshness?: string) => {
    if (!freshness) return 'text-gray-500'
    switch (freshness) {
      case 'real_time':
        return 'text-green-600'
      case 'market_closed':
        return 'text-yellow-600'
      case 'stale':
        return 'text-orange-600'
      case 'error':
        return 'text-red-600'
      case 'mock':
        return 'text-blue-600'
      default:
        return 'text-gray-500'
    }
  }

  const getMarketStatus = () => {
    if (!commoditiesData) return 'Unknown'
    return commoditiesData.market_hours ? 'Market Open' : 'Market Closed'
  }

  return {
    commodities: commoditiesData?.commodities || [],
    isLoading,
    error,
    refresh,
    lastUpdated: getTimeSinceUpdate(),
    dataFreshness: getDataFreshnessColor,
    marketStatus: getMarketStatus(),
    marketHours: commoditiesData?.market_hours || false,
    timestamp: commoditiesData?.timestamp || 0,
    count: commoditiesData?.count || 0,
  }
}
