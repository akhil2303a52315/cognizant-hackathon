import { Eye, Search, BarChart3, Megaphone } from 'lucide-react'
import { useMCPInvoke } from '@/hooks/useMCPTools'
import { useState } from 'react'
import MarkdownRenderer from '@/components/shared/MarkdownRenderer'

export default function Brand() {
  const [brand, setBrand] = useState('')
  const [competitor, setCompetitor] = useState('')
  const invoke = useMCPInvoke()

  const handleSentiment = () => {
    if (!brand.trim()) return
    invoke.mutate({ tool: 'social_sentiment', params: { brand: brand.trim() } })
  }

  const handleCompetitor = () => {
    if (!competitor.trim()) return
    invoke.mutate({ tool: 'competitor_ads', params: { competitor: competitor.trim() } })
  }

  const result = invoke.data?.result as Record<string, unknown> | undefined

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Eye className="w-6 h-6 text-pink-400" />
          Brand Control Center
        </h1>
        <p className="text-gray-400 text-sm">Social sentiment, competitor intelligence, and crisis communications</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Sentiment */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-sm font-semibold text-pink-400 uppercase mb-3 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" /> Sentiment Analysis
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="Brand name..."
              className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-pink-400 focus:outline-none"
            />
            <button onClick={handleSentiment} className="px-3 py-2 bg-pink-500 rounded text-white text-sm hover:bg-pink-600">
              <Search className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Competitor */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-sm font-semibold text-council-purple uppercase mb-3 flex items-center gap-2">
            <Megaphone className="w-4 h-4" /> Competitor Intelligence
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={competitor}
              onChange={(e) => setCompetitor(e.target.value)}
              placeholder="Competitor name..."
              className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-council-purple focus:outline-none"
            />
            <button onClick={handleCompetitor} className="px-3 py-2 bg-council-purple rounded text-white text-sm hover:bg-council-purple-dark">
              <Search className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {invoke.isPending && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-1/3 mb-3" />
          <div className="h-3 bg-gray-700 rounded w-full mb-2" />
          <div className="h-3 bg-gray-700 rounded w-5/6" />
        </div>
      )}

      {result && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-lg font-semibold mb-3">Results</h2>
          <MarkdownRenderer content={`\`\`\`json\n${JSON.stringify(result, null, 2)}\n\`\`\``} />
          {'mock' in result && Boolean(result.mock) && (
            <p className="text-xs text-yellow-500 mt-2">⚠ Using mock data — configure Firecrawl API key for real data</p>
          )}
        </div>
      )}

      {invoke.isError && (
        <div className="bg-risk-red/10 border border-risk-red/30 rounded-lg p-4 text-risk-red text-sm">
          Error: {String(invoke.error ?? 'Unknown error')}
        </div>
      )}
    </div>
  )
}
