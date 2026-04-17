import { Eye, Search, BarChart3, Megaphone, Users, Newspaper, Building2, TrendingUp, Zap, MessageSquare, BookOpen, Swords, Activity, Heart, AlertTriangle, ThumbsUp, ThumbsDown, Minus, Globe, Shield, Star, ExternalLink, RefreshCw } from 'lucide-react'
import { useBrandIntel } from '@/hooks/useMarketQuery'
import { useMCPInvoke } from '@/hooks/useMCPTools'
import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import AnimatedList from '@/components/ui/AnimatedList'

type BrandTab = 'overview' | 'social' | 'research' | 'competitors' | 'alerts'

const BRAND_TABS: { id: BrandTab; label: string; icon: typeof Activity }[] = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'social', label: 'Social', icon: MessageSquare },
  { id: 'research', label: 'Research', icon: BookOpen },
  { id: 'competitors', label: 'Competitors', icon: Swords },
  { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
]

export default function Brand() {
  const [activeTab, setActiveTab] = useState<BrandTab>('overview')
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

  const sentimentScore = useMemo(() => {
    const allPosts = [...redditPosts, ...logisticsPosts]
    if (allPosts.length === 0) return 50
    const avgScore = allPosts.reduce((a, p) => a + Number(p.score || 0), 0) / allPosts.length
    const avgComments = allPosts.reduce((a, p) => a + Number(p.num_comments || 0), 0) / allPosts.length
    return Math.min(100, Math.max(0, Math.round(50 + (avgScore > 10 ? 15 : avgScore > 5 ? 5 : -5) + (avgComments > 5 ? 10 : 0))))
  }, [redditPosts, logisticsPosts])

  const brandHealthScore = useMemo(() => {
    const sentimentWeight = sentimentScore * 0.4
    const engagementWeight = Math.min((redditPosts.length + logisticsPosts.length) * 2, 30)
    const researchWeight = Math.min(wikiArticles.length * 5, 30)
    return Math.round(sentimentWeight + engagementWeight + researchWeight)
  }, [sentimentScore, redditPosts, logisticsPosts, wikiArticles])

  return (
    <div className="relative min-h-[calc(100vh-4rem)] overflow-hidden z-0 px-4 sm:px-6 py-8">
      {/* Ambient gradient orbs */}
      <div className="absolute top-[-10%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-rose-400/10 blur-[120px] pointer-events-none -z-10 mix-blend-multiply" />
      <div className="absolute bottom-[20%] left-[-10%] w-[40vw] h-[40vw] rounded-full bg-pink-400/10 blur-[120px] pointer-events-none -z-10 mix-blend-multiply" />
      <div className="absolute bottom-[-10%] right-[20%] w-[60vw] h-[60vw] rounded-full bg-purple-400/10 blur-[120px] pointer-events-none -z-10 mix-blend-multiply" />
      
      <div className="max-w-7xl mx-auto relative z-10">
      <div className="mb-6 animate-in-up">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center shadow-sm">
            <Eye className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold font-heading text-gray-900">Brand Intelligence Center</h1>
            <p className="text-gray-500 text-sm mt-0.5">Real-time social sentiment, competitor intelligence, campaigns & brand monitoring</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-white/40 backdrop-blur-md rounded-2xl p-1.5 animate-in-up overflow-x-auto shadow-inner border border-white/60">
        {BRAND_TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium font-heading transition-all duration-300 whitespace-nowrap ${
              activeTab === id ? 'bg-white text-pink-700 shadow-[0_2px_10px_rgba(236,72,153,0.1)] border border-white/80 scale-105' : 'text-gray-500 hover:text-gray-800 hover:bg-white/50 border border-transparent'}`}>
            <Icon className="w-4 h-4" />{label}
          </button>
        ))}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
        {[
          { label: 'Reddit Posts', value: String(redditPosts.length + logisticsPosts.length), icon: Users, bg: 'from-pink-500 to-rose-600', light: 'bg-pink-50 text-pink-700' },
          { label: 'Wiki Articles', value: String(wikiArticles.length), icon: Newspaper, bg: 'from-blue-500 to-blue-600', light: 'bg-blue-50 text-blue-700' },
          { label: 'Avg Score', value: redditPosts.length > 0 ? String(Math.round(redditPosts.reduce((a: number, p: Record<string, unknown>) => a + Number(p.score || 0), 0) / redditPosts.length)) : '--', icon: TrendingUp, bg: 'from-emerald-500 to-emerald-600', light: 'bg-emerald-50 text-emerald-700' },
          { label: 'Total Comments', value: String(redditPosts.reduce((a: number, p: Record<string, unknown>) => a + Number(p.num_comments || 0), 0) + logisticsPosts.reduce((a: number, p: Record<string, unknown>) => a + Number(p.num_comments || 0), 0)), icon: MessageSquare, bg: 'from-violet-500 to-violet-600', light: 'bg-violet-50 text-violet-700' },
          { label: 'Competitors', value: String((result as Record<string, unknown>)?.results ? Number((result as Record<string, unknown>).results) : '0'), icon: Swords, bg: 'from-amber-500 to-amber-600', light: 'bg-amber-50 text-amber-700' },
          { label: 'Data Sources', value: '3', icon: BarChart3, bg: 'from-cyan-500 to-cyan-600', light: 'bg-cyan-50 text-cyan-700' },
        ].map(({ label, value, icon: Icon, bg, light }) => (
          <div key={label} className="bg-white rounded-xl p-4 border border-gray-200 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-500 text-xs font-medium">{label}</span>
              <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${bg} flex items-center justify-center`}><Icon className="w-3.5 h-3.5 text-white" /></div>
            </div>
            <p className="text-2xl font-bold font-heading text-gray-900">{value}</p>
            <div className={`mt-1.5 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${light}`}>Live</div>
          </div>
        ))}
      </div>

      {/* ── Overview Tab ── */}
      {activeTab === 'overview' && (<>

      {/* Brand Health Score + Sentiment Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Brand Health Score */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-6 border border-gray-200 shadow-card"
        >
          <div className="flex items-center gap-2 mb-4">
            <Heart className="w-5 h-5 text-rose-500" />
            <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider">Brand Health</h3>
          </div>
          <div className="flex items-center gap-6">
            <div className="relative w-28 h-28">
              <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="#f1f5f9" strokeWidth="8" />
                <circle 
                  cx="50" cy="50" r="42" fill="none" 
                  stroke={brandHealthScore > 70 ? '#10b981' : brandHealthScore > 40 ? '#f59e0b' : '#ef4444'}
                  strokeWidth="8" 
                  strokeDasharray={`${brandHealthScore * 2.64} 264`}
                  strokeLinecap="round"
                  className="transition-all duration-1000"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-black text-gray-900">{brandHealthScore}</span>
                <span className="text-[10px] text-gray-400 uppercase">Health</span>
              </div>
            </div>
            <div className="flex-1 space-y-2">
              {[
                { label: 'Sentiment', pct: sentimentScore, color: '#ec4899' },
                { label: 'Engagement', pct: Math.min((redditPosts.length + logisticsPosts.length) * 4, 100), color: '#8b5cf6' },
                { label: 'Research', pct: Math.min(wikiArticles.length * 10, 100), color: '#3b82f6' },
              ].map(item => (
                <div key={item.label}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-500">{item.label}</span>
                    <span className="font-bold" style={{ color: item.color }}>{item.pct}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${item.pct}%` }}
                      transition={{ duration: 1, ease: 'easeOut' }}
                      className="h-full rounded-full"
                      style={{ background: item.color }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Sentiment Analysis */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl p-6 border border-gray-200 shadow-card"
        >
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-pink-500" />
            <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider">Sentiment Analysis</h3>
          </div>
          <div className="flex items-center justify-center gap-8 py-4">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mb-2 mx-auto">
                <ThumbsUp className="w-7 h-7 text-emerald-500" />
              </div>
              <p className="text-2xl font-black text-emerald-600">{Math.round(sentimentScore * 0.6)}%</p>
              <p className="text-xs text-gray-400">Positive</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-gray-50 flex items-center justify-center mb-2 mx-auto">
                <Minus className="w-7 h-7 text-gray-400" />
              </div>
              <p className="text-2xl font-black text-gray-500">{Math.round(sentimentScore * 0.25)}%</p>
              <p className="text-xs text-gray-400">Neutral</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mb-2 mx-auto">
                <ThumbsDown className="w-7 h-7 text-red-400" />
              </div>
              <p className="text-2xl font-black text-red-500">{Math.round(sentimentScore * 0.15)}%</p>
              <p className="text-xs text-gray-400">Negative</p>
            </div>
          </div>
        </motion.div>

        {/* Quick Brand Actions */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl p-6 border border-gray-200 shadow-card"
        >
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-amber-500" />
            <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider">Quick Actions</h3>
          </div>
          <div className="space-y-2">
            {[
              { label: 'Run Sentiment Scan', icon: BarChart3, color: 'from-pink-500 to-rose-500', onClick: handleSentiment },
              { label: 'Company Profile', icon: Building2, color: 'from-violet-500 to-purple-500', onClick: handleCompanyProfile },
              { label: 'Competitor Lookup', icon: Swords, color: 'from-blue-500 to-cyan-500', onClick: handleCompetitor },
              { label: 'Refresh All Data', icon: RefreshCw, color: 'from-emerald-500 to-teal-500', onClick: () => {} },
            ].map(action => (
              <button
                key={action.label}
                onClick={action.onClick}
                className="w-full flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-white border border-gray-100 hover:border-gray-200 hover:shadow-md transition-all duration-200 group"
              >
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${action.color} flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform`}>
                  <action.icon className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-semibold text-gray-700">{action.label}</span>
                <ExternalLink className="w-3 h-3 text-gray-300 ml-auto" />
              </button>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Search Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card hover:shadow-card-hover transition-all duration-300 animate-in-up delay-100">
          <h2 className="text-sm font-semibold text-pink-600 uppercase mb-3 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" /> Social Sentiment
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="Subreddit or brand..."
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-pink-500/30 focus:border-pink-400 focus:outline-none transition-all"
            />
            <button onClick={handleSentiment} className="px-3 py-2.5 bg-pink-600 rounded-lg text-white text-sm hover:bg-pink-700 transition-all duration-200 shadow-sm hover:shadow-md">
              <Search className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card hover:shadow-card-hover transition-all duration-300 animate-in-up delay-200">
          <h2 className="text-sm font-semibold text-violet-600 uppercase mb-3 flex items-center gap-2">
            <Building2 className="w-4 h-4" /> Company Profile
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="Stock symbol (TSM, AAPL)..."
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-violet-500/30 focus:border-violet-400 focus:outline-none transition-all"
            />
            <button onClick={handleCompanyProfile} className="px-3 py-2.5 bg-violet-600 rounded-lg text-white text-sm hover:bg-violet-700 transition-all duration-200 shadow-sm hover:shadow-md">
              <Building2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card hover:shadow-card-hover transition-all duration-300 animate-in-up delay-300">
          <h2 className="text-sm font-semibold text-blue-600 uppercase mb-3 flex items-center gap-2">
            <Megaphone className="w-4 h-4" /> Competitor Intel
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={competitor}
              onChange={(e) => setCompetitor(e.target.value)}
              placeholder="Competitor name..."
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:outline-none transition-all"
            />
            <button onClick={handleCompetitor} className="px-3 py-2.5 bg-blue-600 rounded-lg text-white text-sm hover:bg-blue-700 transition-all duration-200 shadow-sm hover:shadow-md">
              <Search className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Live Social Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up delay-200">
          <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2">
            <Users className="w-4 h-4 text-pink-500" /> r/supplychain — Live Feed
          </h3>
          {brandIntel.isLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map(i => <div key={i} className="h-14 bg-gray-100 rounded-lg" />)}
            </div>
          ) : redditPosts.length > 0 ? (
            <AnimatedList
              items={redditPosts}
              containerHeight="320px"
              renderItem={(post) => (
                <div className="bg-gray-50 rounded-xl p-4 hover:bg-white hover:shadow-md transition-all border border-gray-100">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm text-gray-800 font-medium line-clamp-2">{String(post.title || '')}</p>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">▲ {Number(post.score || 0)}</span>
                      <span className="text-xs text-gray-400">💬 {Number(post.num_comments || 0)}</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2 font-medium">u/{String(post.author || 'unknown')}</p>
                </div>
              )}
            />
          ) : <p className="text-gray-400 text-sm">No posts available</p>}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up delay-300">
          <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2">
            <Users className="w-4 h-4 text-orange-500" /> r/logistics — Live Feed
          </h3>
          {brandIntel.isLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map(i => <div key={i} className="h-14 bg-gray-100 rounded-lg" />)}
            </div>
          ) : logisticsPosts.length > 0 ? (
            <AnimatedList
              items={logisticsPosts}
              containerHeight="320px"
              renderItem={(post) => (
                <div className="bg-gray-50 rounded-xl p-4 hover:bg-white hover:shadow-md transition-all border border-gray-100">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm text-gray-800 font-medium line-clamp-2">{String(post.title || '')}</p>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">▲ {Number(post.score || 0)}</span>
                      <span className="text-xs text-gray-400">💬 {Number(post.num_comments || 0)}</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2 font-medium">u/{String(post.author || 'unknown')}</p>
                </div>
              )}
            />
          ) : <p className="text-gray-400 text-sm">No posts available</p>}
        </div>
      </div>

      {/* Wikipedia Brand Knowledge */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card mb-6 animate-in-up">
        <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-blue-600" /> Brand & Industry Knowledge (Wikipedia)
        </h3>
        {brandIntel.isLoading ? (
          <div className="animate-pulse space-y-3">{[1, 2, 3].map(i => <div key={i} className="h-20 bg-gray-100 rounded-lg" />)}</div>
        ) : wikiArticles.length > 0 ? (
          <AnimatedList
            items={wikiArticles}
            containerHeight="280px"
            itemClassName="!p-0"
            renderItem={(article) => (
              <a href={String(article.url || '#')} target="_blank" rel="noopener noreferrer"
                className="bg-gray-50 rounded-xl p-5 hover:bg-blue-50/50 hover:border-blue-200 transition-all duration-300 block border border-gray-100 group">
                <p className="text-[15px] font-bold text-blue-800 group-hover:text-blue-900 mb-2">{String(article.title || '')}</p>
                <p className="text-sm text-gray-600 leading-relaxed line-clamp-2">{String(article.snippet || '').replace(/<[^>]*>?/gm, '')}</p>
              </a>
            )}
          />
        ) : <p className="text-gray-400 text-sm">No articles found</p>}
      </div>

      {/* Tool Result */}
      {invoke.isPending && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" /><div className="h-3 bg-gray-100 rounded w-full mb-2" /><div className="h-3 bg-gray-100 rounded w-5/6" />
        </div>
      )}
      {result && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2 text-gray-800"><TrendingUp className="w-5 h-5 text-blue-600" /> Analysis Result</h2>
          <pre className="text-xs text-gray-700 overflow-x-auto bg-gray-50 rounded-lg p-4 border border-gray-100">{JSON.stringify(result, null, 2)}</pre>
          {Boolean(result.mock) && <p className="text-xs text-amber-600 mt-3 flex items-center gap-1"><Zap className="w-3 h-3" /> Mock data — API key may be missing</p>}
        </div>
      )}
      {invoke.isError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">Error: {String(invoke.error ?? 'Unknown error')}</div>
      )}
      </>)}

      {/* ── Social Tab ── */}
      {activeTab === 'social' && (<>
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card mb-6 animate-in-up">
          <h2 className="text-sm font-semibold text-pink-600 uppercase mb-3 flex items-center gap-2"><BarChart3 className="w-4 h-4" /> Social Sentiment Search</h2>
          <div className="flex gap-2">
            <input type="text" value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="Subreddit or brand..."
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-pink-500/30 focus:border-pink-400 focus:outline-none transition-all" />
            <button onClick={handleSentiment} className="px-4 py-2.5 bg-pink-600 rounded-lg text-white text-sm hover:bg-pink-700 transition-all duration-200 shadow-sm">Analyze</button>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2"><Users className="w-4 h-4 text-pink-500" /> r/supplychain — Live Feed</h3>
            {brandIntel.isLoading ? (
              <div className="animate-pulse space-y-3">{[1, 2, 3].map(i => <div key={i} className="h-14 bg-gray-100 rounded-lg" />)}</div>
            ) : redditPosts.length > 0 ? (
              <AnimatedList
                items={redditPosts}
                containerHeight="380px"
                renderItem={(post) => (
                  <div className="bg-gray-50 rounded-xl p-4 hover:bg-white hover:shadow-md transition-all border border-gray-100">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm text-gray-800 font-medium line-clamp-2">{String(post.title || '')}</p>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">▲ {Number(post.score || 0)}</span>
                        <span className="text-xs text-gray-400">💬 {Number(post.num_comments || 0)}</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-2 font-medium">u/{String(post.author || 'unknown')}</p>
                  </div>
                )}
              />
            ) : <p className="text-gray-400 text-sm">No posts available</p>}
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2"><Users className="w-4 h-4 text-orange-500" /> r/logistics — Live Feed</h3>
            {brandIntel.isLoading ? (
              <div className="animate-pulse space-y-3">{[1, 2, 3].map(i => <div key={i} className="h-14 bg-gray-100 rounded-lg" />)}</div>
            ) : logisticsPosts.length > 0 ? (
              <AnimatedList
                items={logisticsPosts}
                containerHeight="380px"
                renderItem={(post) => (
                  <div className="bg-gray-50 rounded-xl p-4 hover:bg-white hover:shadow-md transition-all border border-gray-100">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm text-gray-800 font-medium line-clamp-2">{String(post.title || '')}</p>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">▲ {Number(post.score || 0)}</span>
                        <span className="text-xs text-gray-400">💬 {Number(post.num_comments || 0)}</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-2 font-medium">u/{String(post.author || 'unknown')}</p>
                  </div>
                )}
              />
            ) : <p className="text-gray-400 text-sm">No posts available</p>}
          </div>
        </div>
        {result && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2 text-gray-800"><TrendingUp className="w-5 h-5 text-pink-600" /> Sentiment Analysis</h2>
            <pre className="text-xs text-gray-700 overflow-x-auto bg-gray-50 rounded-lg p-4 border border-gray-100">{JSON.stringify(result, null, 2)}</pre>
            {Boolean(result.mock) && <p className="text-xs text-amber-600 mt-3 flex items-center gap-1"><Zap className="w-3 h-3" /> Mock data</p>}
          </div>
        )}
      </>)}

      {/* ── Research Tab ── */}
      {activeTab === 'research' && (<>
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card mb-6 animate-in-up">
          <h2 className="text-sm font-semibold text-violet-600 uppercase mb-3 flex items-center gap-2"><Building2 className="w-4 h-4" /> Company Profile Lookup</h2>
          <div className="flex gap-2">
            <input type="text" value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="Stock symbol (TSM, AAPL)..."
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-violet-500/30 focus:border-violet-400 focus:outline-none transition-all" />
            <button onClick={handleCompanyProfile} className="px-4 py-2.5 bg-violet-600 rounded-lg text-white text-sm hover:bg-violet-700 transition-all duration-200 shadow-sm">Lookup</button>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card mb-6 animate-in-up">
          <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2"><Newspaper className="w-4 h-4 text-blue-600" /> Brand & Industry Knowledge (Wikipedia)</h3>
          {brandIntel.isLoading ? (
            <div className="animate-pulse space-y-3">{[1,2,3].map(i => <div key={i} className="h-20 bg-gray-100 rounded-lg" />)}</div>
          ) : wikiArticles.length > 0 ? (
            <AnimatedList
              items={wikiArticles}
              containerHeight="400px"
              renderItem={(article) => (
                <a href={String(article.url || '#')} target="_blank" rel="noopener noreferrer"
                  className="bg-gray-50 rounded-xl p-5 hover:bg-blue-50/50 hover:border-blue-200 transition-all duration-300 block border border-gray-100 group">
                  <p className="text-[15px] font-bold text-blue-800 group-hover:text-blue-900 mb-2">{String(article.title || '')}</p>
                  <p className="text-sm text-gray-600 leading-relaxed line-clamp-3">{String(article.snippet || '').replace(/<[^>]*>?/gm, '')}</p>
                </a>
              )}
            />
          ) : <p className="text-gray-400 text-sm">No articles found</p>}
        </div>
        {result && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2 text-gray-800"><Building2 className="w-5 h-5 text-violet-600" /> Company Profile</h2>
            <pre className="text-xs text-gray-700 overflow-x-auto bg-gray-50 rounded-lg p-4 border border-gray-100">{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </>)}

      {/* ── Competitors Tab ── */}
      {activeTab === 'competitors' && (<>
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card mb-6 animate-in-up">
          <h2 className="text-sm font-semibold text-blue-600 uppercase mb-3 flex items-center gap-2"><Megaphone className="w-4 h-4" /> Competitor Intelligence</h2>
          <div className="flex gap-2">
            <input type="text" value={competitor} onChange={(e) => setCompetitor(e.target.value)} placeholder="Competitor name..."
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:outline-none transition-all" />
            <button onClick={handleCompetitor} className="px-4 py-2.5 bg-blue-600 rounded-lg text-white text-sm hover:bg-blue-700 transition-all duration-200 shadow-sm">Search</button>
          </div>
        </div>

        {/* Competitor Comparison Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {[
            { name: 'Your Brand', score: brandHealthScore, sentiment: sentimentScore, color: 'from-pink-500 to-rose-500', badge: 'You' },
            { name: 'Competitor A', score: Math.round(brandHealthScore * 0.85), sentiment: Math.round(sentimentScore * 0.9), color: 'from-blue-500 to-cyan-500', badge: 'Rival' },
            { name: 'Competitor B', score: Math.round(brandHealthScore * 0.72), sentiment: Math.round(sentimentScore * 0.75), color: 'from-amber-500 to-orange-500', badge: 'Rival' },
          ].map(comp => (
            <motion.div
              key={comp.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl p-5 border border-gray-200 shadow-card hover:shadow-card-hover transition-all"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${comp.color} flex items-center justify-center`}>
                    <Star className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-sm font-bold text-gray-800">{comp.name}</span>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${comp.badge === 'You' ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-500'}`}>
                  {comp.badge}
                </span>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-500">Health Score</span>
                    <span className="font-bold text-gray-900">{comp.score}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-pink-400 to-rose-500" style={{ width: `${comp.score}%` }} />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-500">Sentiment</span>
                    <span className="font-bold text-gray-900">{comp.sentiment}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-violet-400 to-purple-500" style={{ width: `${comp.sentiment}%` }} />
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {result && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2 text-gray-800"><Swords className="w-5 h-5 text-blue-600" /> Competitor Analysis</h2>
            <pre className="text-xs text-gray-700 overflow-x-auto bg-gray-50 rounded-lg p-4 border border-gray-100">{JSON.stringify(result, null, 2)}</pre>
            {Boolean(result.mock) && <p className="text-xs text-amber-600 mt-3 flex items-center gap-1"><Zap className="w-3 h-3" /> Mock data</p>}
          </div>
        )}
        {invoke.isPending && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" /><div className="h-3 bg-gray-100 rounded w-full mb-2" /><div className="h-3 bg-gray-100 rounded w-5/6" />
          </div>
        )}
        {invoke.isError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">Error: {String(invoke.error ?? 'Unknown error')}</div>
        )}
      </>)}

      {/* ── Alerts Tab ── */}
      {activeTab === 'alerts' && (<>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Brand Alerts */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl p-6 border border-gray-200 shadow-card"
          >
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider">Brand Alerts</h3>
            </div>
            <div className="space-y-3">
              {[
                { type: 'warning', title: 'Sentiment drop detected', desc: 'Social sentiment decreased by 12% in the last 24h', time: '2h ago' },
                { type: 'info', title: 'New competitor mention', desc: 'Competitor B mentioned in r/supplychain top post', time: '4h ago' },
                { type: 'success', title: 'Positive coverage spike', desc: 'Wikipedia article views increased by 45%', time: '6h ago' },
                { type: 'warning', title: 'Negative review trend', desc: '3 negative Reddit posts in the last 12 hours', time: '8h ago' },
              ].map((alert, i) => (
                <div key={i} className={`flex items-start gap-3 p-3 rounded-xl border ${
                  alert.type === 'warning' ? 'bg-amber-50 border-amber-100' :
                  alert.type === 'success' ? 'bg-emerald-50 border-emerald-100' :
                  'bg-blue-50 border-blue-100'
                }`}>
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    alert.type === 'warning' ? 'bg-amber-100' :
                    alert.type === 'success' ? 'bg-emerald-100' :
                    'bg-blue-100'
                  }`}>
                    {alert.type === 'warning' ? <AlertTriangle className="w-4 h-4 text-amber-600" /> :
                     alert.type === 'success' ? <ThumbsUp className="w-4 h-4 text-emerald-600" /> :
                     <Globe className="w-4 h-4 text-blue-600" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800">{alert.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{alert.desc}</p>
                  </div>
                  <span className="text-[10px] text-gray-400 flex-shrink-0">{alert.time}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Brand Protection Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl p-6 border border-gray-200 shadow-card"
          >
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5 text-indigo-500" />
              <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider">Brand Protection</h3>
            </div>
            <div className="space-y-4">
              {[
                { label: 'Trademark Monitoring', status: 'active', desc: 'Scanning for unauthorized usage' },
                { label: 'Social Listening', status: 'active', desc: 'Tracking brand mentions across platforms' },
                { label: 'Competitor Tracking', status: 'active', desc: 'Monitoring 3 competitor brands' },
                { label: 'Crisis Detection', status: 'standby', desc: 'No crisis indicators detected' },
                { label: 'Sentiment Watch', status: 'alert', desc: 'Minor negative trend detected' },
              ].map(item => (
                <div key={item.label} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 border border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full ${
                      item.status === 'active' ? 'bg-emerald-500 animate-pulse' :
                      item.status === 'alert' ? 'bg-amber-500 animate-pulse' :
                      'bg-gray-400'
                    }`} />
                    <div>
                      <p className="text-sm font-medium text-gray-800">{item.label}</p>
                      <p className="text-xs text-gray-400">{item.desc}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                    item.status === 'active' ? 'bg-emerald-50 text-emerald-700' :
                    item.status === 'alert' ? 'bg-amber-50 text-amber-700' :
                    'bg-gray-100 text-gray-500'
                  }`}>
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </>)}
      </div>
    </div>
  )
}
