import { useQuery, useQueryClient } from '@tanstack/react-query'
import { marketApi } from '@/lib/api'

interface StockQuote {
  symbol: string
  current_price: number
  change: number
  change_percent: number
  high: number
  low: number
  open: number
  prev_close: number
  timestamp: number
  data_freshness: 'real_time' | 'market_closed' | 'stale' | 'error' | 'mock'
  market_hours: boolean
  mock?: boolean
  error?: string
}

interface SupplyChainStocksResponse {
  stocks: StockQuote[]
  timestamp: number
  count: number
  market_hours: boolean
}

export function useSupplyChainStocks(symbols?: string[]) {
  const queryClient = useQueryClient()

  const result = useQuery({
    queryKey: ['market', 'supply-chain-stocks', symbols],
    queryFn: async () => {
      const { data } = await marketApi.supplyChainStocks(symbols)
      return data as SupplyChainStocksResponse
    },
    refetchInterval: 2 * 60 * 1000, // Auto-refresh every 2 minutes
    staleTime: 60 * 1000, // Consider data stale after 60 seconds
    gcTime: 5 * 60 * 1000, // Keep in cache for 5 minutes (garbage collection time)
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })

  const refreshStocks = async () => {
    await queryClient.invalidateQueries({
      queryKey: ['market', 'supply-chain-stocks', symbols]
    })
    await queryClient.refetchQueries({
      queryKey: ['market', 'supply-chain-stocks', symbols]
    })
  }

  const getTimeSinceUpdate = (timestamp: number) => {
    const now = Date.now()
    const diff = now - timestamp * 1000 // Convert to milliseconds
    const minutes = Math.floor(diff / (1000 * 60))
    
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
    
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`
    
    const days = Math.floor(hours / 24)
    return `${days} day${days > 1 ? 's' : ''} ago`
  }

  const getFreshnessLabel = (freshness: StockQuote['data_freshness']) => {
    switch (freshness) {
      case 'real_time':
        return 'Live'
      case 'market_closed':
        return 'Market Closed'
      case 'stale':
        return 'Stale'
      case 'error':
        return 'Error'
      case 'mock':
        return 'Mock Data'
      default:
        return 'Unknown'
    }
  }

  const getFreshnessColor = (freshness: StockQuote['data_freshness']) => {
    switch (freshness) {
      case 'real_time':
        return 'text-emerald-600 bg-emerald-50 border-emerald-200'
      case 'market_closed':
        return 'text-amber-600 bg-amber-50 border-amber-200'
      case 'stale':
        return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'mock':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  return {
    ...result,
    refreshStocks,
    getTimeSinceUpdate,
    getFreshnessLabel,
    getFreshnessColor,
  }
}
