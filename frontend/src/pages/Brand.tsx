import { Eye, Search, BarChart3, Megaphone, Users, Newspaper, Building2, TrendingUp } from 'lucide-react'
import { useBrandIntel } from '@/hooks/useMarketQuery'
import { useMCPInvoke } from '@/hooks/useMCPTools'
import { useState } from 'react'

export default function Brand() {
  const [brand, setBrand] = useState('')
  const [competitor, setCompetitor] = useState('')
  const invoke = useMCPInvoke()
  const brandIntel = useBrandIntel()

  const handleSentiment = () => {
    if (!brand.trim()) return
    invoke.mutate({ tool: 'reddit_sentiment', params: { subreddit: brand.trim().toLowerCase().replace(/\s+/g, ''), limit: 10 } })
  }

  const handleCompetitor = () => {
    if (!competitor.trim()) return
    invoke.mutate({ tool: 'wikipedia_search', params: { query: competitor.trim(), limit: 5 } })
  }

  const handleCompanyProfile = () => {
    if (!brand.trim()) return
    invoke.mutate({ tool: 'company_profile', params: { symbol: brand.trim().toUpperCase() } })
  }

  const result = invoke.data?.result as Record<string, unknown> | undefined

  const redditPosts = ((brandIntel.data?.supplychain_reddit?.posts || []) as Array<Record<string, unknown>>)
  const logisticsPosts = ((brandIntel.data?.logistics_reddit?.posts || []) as Array<Record<string, unknown>>)
  const wikiArticles = ((brandIntel.data?.wiki_articles?.results || []) as Array<Record<string, unknown>>)

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Eye className="w-6 h-6 text-pink-400" />
          Brand Intelligence Center
        </h1>
        <p className="text-gray-400 text-sm mt-1">Real-time social sentiment, competitor intelligence, campaigns & brand monitoring</p>
      </div>

      {/* Search Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-sm font-semibold text-pink-400 uppercase mb-3 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" /> Social Sentiment
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="Subreddit or brand..."
              className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-pink-400 focus:outline-none"
            />
            <button onClick={handleSentiment} className="px-3 py-2 bg-pink-500 rounded text-white text-sm hover:bg-pink-600">
              <Search className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-sm font-semibold text-council-purple uppercase mb-3 flex items-center gap-2">
            <Building2 className="w-4 h-4" /> Company Profile
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="Stock symbol (TSM, AAPL)..."
              className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-council-purple focus:outline-none"
            />
            <button onClick={handleCompanyProfile} className="px-3 py-2 bg-council-purple rounded text-white text-sm hover:bg-purple-700">
              <Building2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-sm font-semibold text-supply-blue uppercase mb-3 flex items-center gap-2">
            <Megaphone className="w-4 h-4" /> Competitor Intel
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={competitor}
              onChange={(e) => setCompetitor(e.target.value)}
              placeholder="Competitor name..."
              className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-supply-blue focus:outline-none"
            />
            <button onClick={handleCompetitor} className="px-3 py-2 bg-supply-blue rounded text-white text-sm hover:bg-blue-600">
              <Search className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Live Social Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-900/80 rounded-lg border border-gray-800 p-4">
          <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-pink-400" /> r/supplychain — Live Feed
          </h3>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {brandIntel.isLoading ? (
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map(i => <div key={i} className="h-12 bg-gray-800 rounded" />)}
              </div>
            ) : redditPosts.length > 0 ? redditPosts.map((post, i) => (
              <div key={i} className="bg-gray-800/50 rounded p-3 hover:bg-gray-800 transition-colors">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm text-gray-200 font-medium">{String(post.title || '')}</p>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-green-400">▲ {Number(post.score || 0)}</span>
                    <span className="text-xs text-gray-500">💬 {Number(post.num_comments || 0)}</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-1">u/{String(post.author || 'unknown')}</p>
              </div>
            )) : <p className="text-gray-500 text-sm">No posts available</p>}
          </div>
        </div>

        <div className="bg-gray-900/80 rounded-lg border border-gray-800 p-4">
          <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-orange-400" /> r/logistics — Live Feed
          </h3>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {brandIntel.isLoading ? (
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map(i => <div key={i} className="h-12 bg-gray-800 rounded" />)}
              </div>
            ) : logisticsPosts.length > 0 ? logisticsPosts.map((post, i) => (
              <div key={i} className="bg-gray-800/50 rounded p-3 hover:bg-gray-800 transition-colors">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm text-gray-200 font-medium">{String(post.title || '')}</p>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-green-400">▲ {Number(post.score || 0)}</span>
                    <span className="text-xs text-gray-500">💬 {Number(post.num_comments || 0)}</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-1">u/{String(post.author || 'unknown')}</p>
              </div>
            )) : <p className="text-gray-500 text-sm">No posts available</p>}
          </div>
        </div>
      </div>

      {/* Wikipedia Brand Knowledge */}
      <div className="bg-gray-900/80 rounded-lg border border-gray-800 p-4 mb-6">
        <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-supply-blue" /> Brand & Industry Knowledge (Wikipedia)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {brandIntel.isLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map(i => <div key={i} className="h-16 bg-gray-800 rounded" />)}
            </div>
          ) : wikiArticles.length > 0 ? wikiArticles.map((article, i) => (
            <a key={i} href={String(article.url || '#')} target="_blank" rel="noopener noreferrer"
              className="bg-gray-800/50 rounded p-3 hover:bg-gray-800 transition-colors block">
              <p className="text-sm font-medium text-supply-blue">{String(article.title || '')}</p>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{String(article.snippet || '')}</p>
            </a>
          )) : <p className="text-gray-500 text-sm col-span-3">No articles found</p>}
        </div>
      </div>

      {/* Tool Result */}
      {invoke.isPending && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-1/3 mb-3" />
          <div className="h-3 bg-gray-700 rounded w-full mb-2" />
          <div className="h-3 bg-gray-700 rounded w-5/6" />
        </div>
      )}

      {result && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-supply-blue" /> Analysis Result
          </h2>
          <pre className="text-xs text-gray-300 overflow-x-auto bg-gray-800 rounded p-3">
            {JSON.stringify(result, null, 2)}
          </pre>
          {Boolean(result.mock) && (
            <p className="text-xs text-yellow-500 mt-2">⚠ Mock data — API key may be missing</p>
          )}
        </div>
      )}

      {invoke.isError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          Error: {String(invoke.error ?? 'Unknown error')}
        </div>
      )}
    </div>
  )
}
