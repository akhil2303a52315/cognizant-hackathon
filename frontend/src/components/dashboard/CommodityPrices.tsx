import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'
import { useCommodities, CommodityData } from '@/hooks/useCommodities'

// Commodity emoji mapping
const commodityEmojis: Record<string, string> = {
  'Gold': '🪙',
  'Silver': '⚪',
  'Copper': '🟠',
  'Platinum': '💎',
  'Crude Oil': '⛽',
  'Diesel': '🛢️'
}

// Simple SVG sparkline component
const SparklineChart: React.FC<{ data: number[]; change: number }> = ({ data, change }) => {
  if (!data || data.length < 2) {
    return <div className="h-8 bg-gray-100 rounded animate-pulse" />
  }

  const width = 120
  const height = 32
  const padding = 4
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * chartWidth
    const y = padding + (1 - (value - min) / range) * chartHeight
    return `${x},${y}`
  }).join(' ')

  const color = change >= 0 ? '#10b981' : '#ef4444'

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={0.8}
      />
      <polyline
        points={`${points} ${width - padding},${height - padding} ${padding},${height - padding}`}
        fill={color}
        opacity={0.1}
      />
    </svg>
  )
}

// Loading skeleton component
const CommodityCardSkeleton: React.FC = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="bg-white rounded-xl shadow-lg border border-gray-200 p-6"
  >
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-gray-200 rounded-full animate-pulse" />
        <div>
          <div className="h-4 bg-gray-200 rounded w-20 mb-1 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded w-16 animate-pulse" />
        </div>
      </div>
      <div className="h-6 bg-gray-200 rounded w-16 animate-pulse" />
    </div>
    <div className="space-y-3">
      <div className="h-8 bg-gray-200 rounded w-24 animate-pulse" />
      <div className="h-4 bg-gray-200 rounded w-20 animate-pulse" />
      <div className="h-8 bg-gray-200 rounded animate-pulse" />
      <div className="h-3 bg-gray-200 rounded w-28 animate-pulse" />
    </div>
  </motion.div>
)

// Individual commodity card
const CommodityCard: React.FC<{ commodity: CommodityData }> = ({ commodity }) => {
  const isPositive = commodity.change >= 0
  const TrendIcon = isPositive ? TrendingUp : TrendingDown
  
  // Generate mock historical data for sparkline
  const sparklineData = useMemo(() => {
    const basePrice = commodity.current_price
    const volatility = basePrice * 0.02
    return Array.from({ length: 7 }, (_, i) => {
      const randomChange = (Math.random() - 0.5) * volatility
      return basePrice + randomChange - (commodity.change * (6 - i) / 6)
    })
  }, [commodity.current_price, commodity.change])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)' }}
      className={`bg-white rounded-xl shadow-lg border p-6 transition-all duration-300 ${
        isPositive ? 'border-green-200' : 'border-red-200'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold ${
            isPositive ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
          }`}>
            {commodityEmojis[commodity.name] || commodity.name[0]}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{commodity.name}</h3>
            <p className="text-sm text-gray-500">{commodity.category} ({commodity.unit})</p>
          </div>
        </div>
        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-sm font-medium ${
          isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          <TrendIcon className="w-3 h-3" />
          <span>{isPositive ? '+' : ''}{commodity.change_percent.toFixed(2)}%</span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-gray-900">
            ₹{commodity.current_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}{commodity.change_percent.toFixed(2)}%
          </span>
        </div>

        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>H: ₹{commodity.high.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          <span>L: ₹{commodity.low.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>

        <div className="h-8">
          <SparklineChart data={sparklineData} change={commodity.change} />
        </div>

        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Prev: ₹{commodity.prev_close.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          <span>
            {commodity.error ? (
              <span className="text-red-500 flex items-center">
                <AlertCircle className="w-3 h-3 mr-1" />
                Error
              </span>
            ) : (
              new Date(commodity.timestamp * 1000).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })
            )}
          </span>
        </div>
      </div>
    </motion.div>
  )
}

export const CommodityPrices: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(0)
  const {
    commodities,
    isLoading,
    error,
    refresh,
    lastUpdated,
    marketHours,
    count
  } = useCommodities()

  const COMMODITIES_PER_PAGE = 3
  const totalPages = Math.ceil(count / COMMODITIES_PER_PAGE)
  const startIndex = currentPage * COMMODITIES_PER_PAGE
  const endIndex = Math.min(startIndex + COMMODITIES_PER_PAGE, count)
  const paginatedCommodities = commodities.slice(startIndex, endIndex)

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1)
    }
  }

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1)
    }
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-xl shadow-lg border border-red-200 p-6"
      >
        <div className="flex items-center justify-center space-x-2 text-red-600">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load commodity prices</span>
          <button
            onClick={() => refresh()}
            className="px-3 py-1 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
          >
            Retry
          </button>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Commodity Prices</h2>
          <p className="text-sm text-gray-600">Live global commodity market impact</p>
        </div>
        <div className="flex items-center space-x-3">
          <span className={`text-sm font-medium ${marketHours ? 'text-green-600' : 'text-gray-500'}`}>
            {marketHours ? 'Market Open' : 'Market Closed'}
          </span>
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Last: {lastUpdated}
            </span>
          )}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => refresh()}
            disabled={isLoading}
            className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </motion.button>
        </div>
      </div>

      {/* Commodity Cards with Navigation */}
      <div className="relative">
        <div className="flex items-center gap-4">
          {/* Left Arrow */}
          {!isLoading && currentPage > 0 && (
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handlePreviousPage}
              className="flex-shrink-0 p-3 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </motion.button>
          )}
          
          {/* Cards Grid */}
          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence mode="wait">
              {isLoading ? (
                Array.from({ length: 3 }, (_, i) => (
                  <CommodityCardSkeleton key={`skeleton-${i}`} />
                ))
              ) : (
                paginatedCommodities.map((commodity) => (
                  <CommodityCard
                    key={commodity.symbol}
                    commodity={commodity}
                  />
                ))
              )}
            </AnimatePresence>
          </div>
          
          {/* Right Arrow */}
          {!isLoading && currentPage < totalPages - 1 && (
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handleNextPage}
              className="flex-shrink-0 p-3 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </motion.button>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-sm text-gray-500 pt-4 border-t">
        Prices powered by Yahoo Finance × SupplyChainGPT (in INR)
      </div>
    </motion.div>
  )
}
