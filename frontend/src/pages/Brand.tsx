import { Eye, Search, BarChart3, Megaphone, Users, Newspaper, Building2, TrendingUp, Zap, MessageSquare, BookOpen, Swords, Activity } from 'lucide-react'
import { useBrandIntel } from '@/hooks/useMarketQuery'
import { useMCPInvoke } from '@/hooks/useMCPTools'
import { useState } from 'react'
import AnimatedList from '@/components/ui/AnimatedList'

type BrandTab = 'overview' | 'social' | 'research' | 'competitors'

const BRAND_TABS: { id: BrandTab; label: string; icon: typeof Activity }[] = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'social', label: 'Social', icon: MessageSquare },
  { id: 'research', label: 'Research', icon: BookOpen },
  { id: 'competitors', label: 'Competitors', icon: Swords },
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
      </div>
    </div>
  )
}
