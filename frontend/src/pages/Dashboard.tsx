import { useState } from 'react'
import { Shield, TrendingUp, AlertTriangle, DollarSign, Activity, Globe, Thermometer, Waves, Zap, ArrowUpRight, ArrowDownRight, Layers, Database, Server, HardDrive, Cpu, FileText, Truck, Package, Clock, BarChart3, CheckCircle2, XCircle, AlertCircle, Users } from 'lucide-react'
import { useMarketTicker, useRiskDashboard } from '@/hooks/useMarketQuery'
import { useSuppliers, useRiskHeatmap, useSystemHealth, useRAGStats, useIngestStatus, useModelsStatus } from '@/hooks/useDashboardData'
import LoadingSkeleton from '@/components/shared/LoadingSkeleton'
import AnimatedList from '@/components/ui/AnimatedList'

type TabId = 'overview' | 'market' | 'risk' | 'supply' | 'system'

const TABS: { id: TabId; label: string; icon: typeof Activity }[] = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'market', label: 'Market', icon: TrendingUp },
  { id: 'risk', label: 'Risk', icon: Shield },
  { id: 'supply', label: 'Supply Chain', icon: Truck },
  { id: 'system', label: 'System', icon: Server },
]

function StockCard({ stock }: { stock: Record<string, unknown> }) {
  const price = Number(stock.current_price || 0)
  const change = Number(stock.change_percent || 0)
  const symbol = String(stock.symbol || '???')
  const isUp = change >= 0
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 card-shine min-w-[160px]">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-bold text-blue-700">{symbol}</span>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full flex items-center gap-0.5 ${isUp ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
          {isUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
          {Math.abs(change).toFixed(2)}%
        </span>
      </div>
      <p className="text-2xl font-bold text-gray-900">${price.toFixed(2)}</p>
      {Boolean(stock.mock) && <p className="text-xs text-amber-600 mt-1 flex items-center gap-1"><Zap className="w-3 h-3" /> Mock data</p>}
    </div>
  )
}

function ForexCard({ forex }: { forex: Record<string, unknown> }) {
  const rates = (forex.rates || {}) as Record<string, number>
  const base = String(forex.base || 'USD')
  const flagMap: Record<string, string> = { EUR: '🇪🇺', CNY: '🇨🇳', JPY: '🇯🇵', TWD: '🇹🇼', KRW: '🇰🇷', GBP: '🇬🇧' }
  return (
    <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-card hover:shadow-card-hover transition-all duration-300">
      <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2">
        <DollarSign className="w-4 h-4 text-blue-600" /> Forex Rates (1 {base})
      </h3>
      <div className="grid grid-cols-3 gap-3">
        {Object.entries(rates).map(([cur, val]) => (
          <div key={cur} className="text-center p-2 rounded-lg bg-gray-50 hover:bg-blue-50 transition-colors">
            <span className="text-lg">{flagMap[cur] || '💱'}</span>
            <p className="text-xs text-gray-500 font-medium">{cur}</p>
            <p className="text-sm font-bold text-gray-900">{Number(val).toFixed(cur === 'JPY' || cur === 'KRW' ? 1 : 4)}</p>
          </div>
        ))}
      </div>
      {Boolean(forex.mock) && <p className="text-xs text-amber-600 mt-3 flex items-center gap-1"><Zap className="w-3 h-3" /> Mock</p>}
    </div>
  )
}

function CommodityCard({ commodity }: { commodity: Record<string, unknown> }) {
  const name = String(commodity.commodity || '???').replace(/_/g, ' ')
  const price = Number(commodity.price || 0)
  const source = String(commodity.source || commodity.series_id || '')
  return (
    <div className="bg-white rounded-lg p-3.5 border border-gray-200 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-300 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium capitalize text-gray-900">{name}</p>
        <p className="text-xs text-gray-400">{source}</p>
      </div>
      <p className="text-lg font-bold text-gray-900">${price.toFixed(2)}</p>
    </div>
  )
}

function EarthquakeAlert({ region }: { region: Record<string, unknown> }) {
  const name = String(region.name || 'Unknown')
  const eq = (region.earthquakes || {}) as Record<string, unknown>
  const quakes = (eq.earthquakes || []) as Array<Record<string, unknown>>
  const wx = (region.weather || {}) as Record<string, unknown>
  const forecast = (wx.forecast || []) as Array<Record<string, unknown>>
  const today = forecast[0]
  return (
    <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-card hover:shadow-card-hover transition-all duration-300">
      <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 text-gray-700">
        <Globe className="w-4 h-4 text-violet-600" /> {name}
      </h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-400 mb-1 flex items-center gap-1"><Waves className="w-3 h-3" /> Earthquakes (30d)</p>
          <p className="text-lg font-bold text-red-600">{quakes.length}</p>
          {quakes.slice(0, 2).map((q, i) => (
            <p key={i} className="text-xs text-gray-500">M{Number(q.magnitude).toFixed(1)} — {String(q.place || '').slice(0, 30)}</p>
          ))}
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1 flex items-center gap-1"><Thermometer className="w-3 h-3" /> Today's Weather</p>
          {today ? (
            <>
              <p className="text-sm text-gray-900">{Number(today.temp_max).toFixed(0)}°C / {Number(today.temp_min).toFixed(0)}°C</p>
              <p className="text-xs text-gray-500">🌧 {Number(today.precipitation || 0).toFixed(1)}mm</p>
            </>
          ) : <p className="text-xs text-gray-400">No data</p>}
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const ticker = useMarketTicker()
  const risk = useRiskDashboard()
  const suppliers = useSuppliers()
  const heatmap = useRiskHeatmap()
  const systemHealth = useSystemHealth()
  const ragStats = useRAGStats()
  const ingestStatus = useIngestStatus()
  const modelsStatus = useModelsStatus()

  const stocks = (ticker.data?.stocks || []) as Array<Record<string, unknown>>
  const forex = (ticker.data?.forex || {}) as Record<string, unknown>
  const commodities = (ticker.data?.commodities || []) as Array<Record<string, unknown>>
  const regions = (risk.data?.regions || []) as Array<Record<string, unknown>>
  const disasters = (risk.data?.global_disasters?.alerts || []) as Array<Record<string, unknown>>
  const supplierList = (suppliers.data?.suppliers || []) as Array<Record<string, unknown>>
  const heatmapRegions = (heatmap.data?.regions || {}) as Record<string, number>
  const healthChecks = (systemHealth.data?.data?.checks || {}) as Record<string, string>
  const avgRisk = heatmap.data?.global_avg ? Number(heatmap.data.global_avg).toFixed(1) : '--'
  const supplierCount = supplierList.length || 3
  const healthyServices = Object.values(healthChecks).filter(v => v === 'ok').length
  const totalServices = Object.keys(healthChecks).length || 1

  return (
    <div className="relative min-h-[calc(100vh-4rem)] overflow-hidden z-0 px-4 sm:px-6 py-8">
      {/* Ambient gradient orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-blue-400/10 blur-[120px] pointer-events-none -z-10 mix-blend-multiply" />
      <div className="absolute top-[20%] right-[-10%] w-[40vw] h-[40vw] rounded-full bg-violet-400/10 blur-[120px] pointer-events-none -z-10 mix-blend-multiply" />
      <div className="absolute bottom-[-10%] left-[20%] w-[60vw] h-[60vw] rounded-full bg-cyan-400/10 blur-[120px] pointer-events-none -z-10 mix-blend-multiply" />
      
      <div className="max-w-7xl mx-auto relative z-10">
      {/* Hero Header */}
      <div className="mb-6 animate-in-up">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-glow-blue">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold font-heading text-gradient">Supply Chain Command Center</h1>
            <p className="text-gray-500 text-sm mt-0.5">Real-time market data, risk monitoring & council insights</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-white/40 backdrop-blur-md rounded-2xl p-1.5 animate-in-up overflow-x-auto shadow-inner border border-white/60">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium font-heading transition-all duration-300 whitespace-nowrap ${
              activeTab === id
                ? 'bg-white text-blue-700 shadow-[0_2px_10px_rgba(37,99,235,0.1)] border border-white/80 scale-105'
                : 'text-gray-500 hover:text-gray-800 hover:bg-white/50 border border-transparent'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* KPI Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 mb-6">
        {[
          { label: 'MCP Tools', value: '99', icon: Layers, bg: 'from-blue-500 to-blue-600', light: 'bg-blue-50 text-blue-700' },
          { label: 'Live APIs', value: '27', icon: Globe, bg: 'from-emerald-500 to-emerald-600', light: 'bg-emerald-50 text-emerald-700' },
          { label: 'Risk Regions', value: String(regions.length || 3), icon: Shield, bg: 'from-red-500 to-red-600', light: 'bg-red-50 text-red-700' },
          { label: 'Data Sources', value: '40+', icon: Database, bg: 'from-violet-500 to-violet-600', light: 'bg-violet-50 text-violet-700' },
          { label: 'Suppliers', value: String(supplierCount), icon: Users, bg: 'from-cyan-500 to-cyan-600', light: 'bg-cyan-50 text-cyan-700' },
          { label: 'Avg Risk', value: String(avgRisk), icon: BarChart3, bg: 'from-amber-500 to-amber-600', light: 'bg-amber-50 text-amber-700' },
          { label: 'Disasters', value: String(disasters.length), icon: AlertTriangle, bg: 'from-rose-500 to-rose-600', light: 'bg-rose-50 text-rose-700' },
          { label: 'Services Up', value: `${healthyServices}/${totalServices}`, icon: CheckCircle2, bg: 'from-teal-500 to-teal-600', light: 'bg-teal-50 text-teal-700' },
        ].map(({ label, value, icon: Icon, bg, light }) => (
          <div key={label} className="bg-white/70 backdrop-blur-xl rounded-2xl p-5 border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-500 card-shine">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-500 text-xs font-medium">{label}</span>
              <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${bg} flex items-center justify-center`}>
                <Icon className="w-3.5 h-3.5 text-white" />
              </div>
            </div>
            <p className="text-2xl font-bold font-heading text-gray-900">{value}</p>
            <div className={`mt-1.5 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${light}`}>Active</div>
          </div>
        ))}
      </div>

      {/* ── Overview Tab ── */}
      {activeTab === 'overview' && (<>
        <div className="mb-6 bg-white/60 backdrop-blur-xl rounded-2xl border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-5 animate-in-up">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Live Market Ticker</span>
            {ticker.isFetching && <span className="text-xs text-blue-600 animate-pulse font-medium">Updating...</span>}
          </div>
          <div className="flex gap-3 overflow-x-auto pb-1">
            {ticker.isLoading ? <LoadingSkeleton variant="card" count={4} /> : stocks.map((s, i) => <StockCard key={i} stock={s} />)}
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="animate-in-up">{ticker.isLoading ? <LoadingSkeleton variant="card" /> : <ForexCard forex={forex} />}</div>
          <div className="lg:col-span-2 animate-in-up">
            <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-card">
              <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2"><TrendingUp className="w-4 h-4 text-blue-600" /> Commodity Prices</h3>
              <div className="space-y-2">{ticker.isLoading ? <LoadingSkeleton variant="card" count={2} /> : commodities.map((c, i) => <CommodityCard key={i} commodity={c} />)}</div>
            </div>
          </div>
        </div>
        <div className="mb-6 animate-in-up">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-800">
            <div className="w-6 h-6 rounded-md bg-red-100 flex items-center justify-center"><Shield className="w-3.5 h-3.5 text-red-600" /></div>
            Supply Chain Risk Monitor
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {risk.isLoading ? <LoadingSkeleton variant="card" count={3} /> : regions.map((r, i) => <EarthquakeAlert key={i} region={r} />)}
          </div>
        </div>
        {disasters.length > 0 && (
          <div className="bg-red-50/50 backdrop-blur-md rounded-2xl p-6 border border-red-200/60 mb-6 animate-in-up">
            <h3 className="text-sm font-black text-red-800 uppercase tracking-wider mb-5 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" /> Global Disaster Alerts (GDACS)
            </h3>
            <AnimatedList
              items={disasters}
              containerHeight="350px"
              renderItem={(d) => (
                <div className="flex items-center justify-between text-[15px] bg-white rounded-xl p-4 border border-red-100 shadow-sm hover:shadow-md transition-all group">
                  <span className="text-gray-900 font-medium group-hover:text-red-700 transition-colors">{String(d.title || '')}</span>
                  <span className="text-xs text-gray-400 font-mono bg-gray-50 px-2 py-1 rounded-lg border border-gray-100">{String(d.date || '')}</span>
                </div>
              )}
            />
          </div>
        )}
      </>)}

      {/* ── Market Tab ── */}
      {activeTab === 'market' && (<>
        <div className="mb-6 bg-white/60 backdrop-blur-xl rounded-2xl border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-5 animate-in-up">
          <div className="flex items-center gap-2 mb-3"><div className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" /><span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Stock Prices</span></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{ticker.isLoading ? <LoadingSkeleton variant="card" count={4} /> : stocks.map((s, i) => <StockCard key={i} stock={s} />)}</div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="animate-in-up">{ticker.isLoading ? <LoadingSkeleton variant="card" /> : <ForexCard forex={forex} />}</div>
          <div className="animate-in-up">
            <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-card">
              <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2"><TrendingUp className="w-4 h-4 text-blue-600" /> Commodity Prices</h3>
              <div className="space-y-2">{ticker.isLoading ? <LoadingSkeleton variant="card" count={2} /> : commodities.map((c, i) => <CommodityCard key={i} commodity={c} />)}</div>
            </div>
          </div>
        </div>
      </>)}

      {/* ── Risk Tab ── */}
      {activeTab === 'risk' && (<>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">Avg Risk Score</span><BarChart3 className="w-4 h-4 text-amber-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{avgRisk}</p><p className="text-xs text-gray-400 mt-1">Threshold: 40</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">High Risk Regions</span><AlertTriangle className="w-4 h-4 text-red-600" /></div>
            <p className="text-2xl font-bold text-red-600">{Object.values(heatmapRegions).filter(v => v > 40).length}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">Disaster Alerts</span><AlertCircle className="w-4 h-4 text-rose-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{disasters.length}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">Risk Regions</span><Globe className="w-4 h-4 text-violet-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{regions.length || 3}</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {risk.isLoading ? <LoadingSkeleton variant="card" count={3} /> : regions.map((r, i) => <EarthquakeAlert key={i} region={r} />)}
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-card mb-6 animate-in-up">
          <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2"><Shield className="w-4 h-4 text-red-600" /> Risk Heatmap by Region</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(heatmapRegions).map(([region, score]) => (
              <div key={region} className={`rounded-lg p-4 text-center border ${score > 40 ? 'bg-red-50 border-red-200' : score > 20 ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200'}`}>
                <p className="text-sm font-medium text-gray-700">{region}</p>
                <p className={`text-2xl font-bold ${score > 40 ? 'text-red-600' : score > 20 ? 'text-amber-600' : 'text-emerald-600'}`}>{Number(score).toFixed(1)}</p>
              </div>
            ))}
          </div>
        </div>
        {disasters.length > 0 && (
          <div className="bg-red-50 rounded-xl p-5 border border-red-200 animate-in-up">
            <h3 className="text-sm font-semibold text-red-700 mb-3 flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Global Disaster Alerts</h3>
            <div className="space-y-2">{disasters.slice(0, 5).map((d, i) => (
              <div key={i} className="flex items-center justify-between text-sm bg-white rounded-lg p-3 border border-red-100">
                <span className="text-gray-800">{String(d.title || '')}</span><span className="text-xs text-gray-400">{String(d.date || '')}</span>
              </div>))}</div>
          </div>
        )}
      </>)}

      {/* ── Supply Chain Tab ── */}
      {activeTab === 'supply' && (<>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">Total Suppliers</span><Users className="w-4 h-4 text-cyan-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{supplierCount}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">Avg Lead Time</span><Clock className="w-4 h-4 text-blue-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{supplierList.length > 0 ? Math.round(supplierList.reduce((a: number, s: Record<string, unknown>) => a + Number(s.lead_time_days || 0), 0) / supplierList.length) : '--'}d</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">Avg Capability</span><Package className="w-4 h-4 text-emerald-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{supplierList.length > 0 ? Math.round(supplierList.reduce((a: number, s: Record<string, unknown>) => a + Number(s.capability_match || 0), 0) / supplierList.length) : '--'}%</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">Avg Risk</span><BarChart3 className="w-4 h-4 text-amber-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{avgRisk}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-card mb-6 animate-in-up">
          <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2"><Truck className="w-4 h-4 text-cyan-600" /> Supplier Directory</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-gray-200">
                <th className="text-left py-2 px-3 text-gray-500 font-medium">Name</th>
                <th className="text-left py-2 px-3 text-gray-500 font-medium">Location</th>
                <th className="text-left py-2 px-3 text-gray-500 font-medium">Tier</th>
                <th className="text-left py-2 px-3 text-gray-500 font-medium">Capability</th>
                <th className="text-left py-2 px-3 text-gray-500 font-medium">Lead Time</th>
                <th className="text-left py-2 px-3 text-gray-500 font-medium">Risk</th>
              </tr></thead>
              <tbody>
                {suppliers.isLoading ? <tr><td colSpan={6} className="py-4 text-center text-gray-400">Loading...</td></tr> :
                  supplierList.map((s, i) => {
                    const riskScore = Number(s.risk_score || 0)
                    return (<tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2.5 px-3 font-medium text-gray-900">{String(s.name || '')}</td>
                      <td className="py-2.5 px-3 text-gray-600">{String(s.location || '')}</td>
                      <td className="py-2.5 px-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${Number(s.tier) === 1 ? 'bg-blue-50 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>Tier {String(s.tier)}</span></td>
                      <td className="py-2.5 px-3">{Number(s.capability_match || 0)}%</td>
                      <td className="py-2.5 px-3">{Number(s.lead_time_days || 0)}d</td>
                      <td className="py-2.5 px-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${riskScore > 40 ? 'bg-red-50 text-red-700' : riskScore > 20 ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}`}>{riskScore}</span></td>
                    </tr>)
                  })}
              </tbody>
            </table>
          </div>
        </div>
      </>)}

      {/* ── System Tab ── */}
      {activeTab === 'system' && (<>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">Services Up</span><CheckCircle2 className="w-4 h-4 text-teal-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{healthyServices}/{totalServices}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">MCP Tools</span><Layers className="w-4 h-4 text-blue-600" /></div>
            <p className="text-2xl font-bold text-gray-900">99</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">RAG Docs</span><FileText className="w-4 h-4 text-violet-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{String(ragStats.data?.document_count ?? ragStats.data?.total_documents ?? '--')}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-card">
            <div className="flex items-center justify-between mb-2"><span className="text-gray-500 text-xs font-medium">Ingest Status</span><HardDrive className="w-4 h-4 text-emerald-600" /></div>
            <p className="text-2xl font-bold text-gray-900">{String(ingestStatus.data?.status ?? 'Idle')}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-card mb-6 animate-in-up">
          <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2"><Server className="w-4 h-4 text-blue-600" /> Service Health Checks</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {Object.entries(healthChecks).map(([name, status]) => (
              <div key={name} className={`rounded-lg p-3 border ${status === 'ok' ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
                <div className="flex items-center gap-2 mb-1">
                  {status === 'ok' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <XCircle className="w-4 h-4 text-red-600" />}
                  <span className="text-sm font-medium text-gray-700">{name.replace(/_/g, ' ')}</span>
                </div>
                <p className={`text-xs font-medium ${status === 'ok' ? 'text-emerald-600' : 'text-red-600'}`}>{status === 'ok' ? 'Healthy' : 'Error'}</p>
              </div>
            ))}
            {Object.keys(healthChecks).length === 0 && <p className="text-gray-400 text-sm col-span-5">Loading health checks...</p>}
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-card animate-in-up">
          <h3 className="text-sm font-semibold text-gray-500 mb-4 flex items-center gap-2"><Cpu className="w-4 h-4 text-violet-600" /> AI Models Status</h3>
          <div className="space-y-2">
            {modelsStatus.isLoading ? <p className="text-gray-400 text-sm">Loading models...</p> :
              Object.entries(modelsStatus.data as Record<string, unknown> || {}).slice(0, 6).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between bg-gray-50 rounded-lg p-3 border border-gray-100">
                  <span className="text-sm font-medium text-gray-700">{key}</span>
                  <span className="text-xs text-gray-500">{String(val)}</span>
                </div>
              ))}
          </div>
        </div>
      </>)}
      </div>
    </div>
  )
}
