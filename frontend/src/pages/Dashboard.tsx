import { Shield, TrendingUp, AlertTriangle, DollarSign, Activity, Globe, Thermometer, Waves } from 'lucide-react'
import { useMarketTicker, useRiskDashboard } from '@/hooks/useMarketQuery'
import LoadingSkeleton from '@/components/shared/LoadingSkeleton'

function StockCard({ stock }: { stock: Record<string, unknown> }) {
  const price = Number(stock.current_price || 0)
  const change = Number(stock.change_percent || 0)
  const symbol = String(stock.symbol || '???')
  const isUp = change >= 0
  return (
    <div className="bg-gray-900/80 rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-colors">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-bold text-supply-blue">{symbol}</span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded ${isUp ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
          {isUp ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
        </span>
      </div>
      <p className="text-xl font-bold">${price.toFixed(2)}</p>
      {Boolean(stock.mock) && <p className="text-xs text-yellow-500 mt-1">⚠ Mock data</p>}
    </div>
  )
}

function ForexCard({ forex }: { forex: Record<string, unknown> }) {
  const rates = (forex.rates || {}) as Record<string, number>
  const base = String(forex.base || 'USD')
  const flagMap: Record<string, string> = { EUR: '🇪🇺', CNY: '🇨🇳', JPY: '🇯🇵', TWD: '🇹🇼', KRW: '🇰🇷', GBP: '🇬🇧' }
  return (
    <div className="bg-gray-900/80 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
        <DollarSign className="w-4 h-4 text-supply-blue" /> Forex Rates (1 {base})
      </h3>
      <div className="grid grid-cols-3 gap-2">
        {Object.entries(rates).map(([cur, val]) => (
          <div key={cur} className="text-center">
            <span className="text-lg">{flagMap[cur] || '💱'}</span>
            <p className="text-xs text-gray-500">{cur}</p>
            <p className="text-sm font-semibold">{Number(val).toFixed(cur === 'JPY' || cur === 'KRW' ? 1 : 4)}</p>
          </div>
        ))}
      </div>
      {Boolean(forex.mock) && <p className="text-xs text-yellow-500 mt-2">⚠ Mock</p>}
    </div>
  )
}

function CommodityCard({ commodity }: { commodity: Record<string, unknown> }) {
  const name = String(commodity.commodity || '???').replace(/_/g, ' ')
  const price = Number(commodity.price || 0)
  const source = String(commodity.source || commodity.series_id || '')
  return (
    <div className="bg-gray-900/80 rounded-lg p-3 border border-gray-800 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium capitalize">{name}</p>
        <p className="text-xs text-gray-500">{source}</p>
      </div>
      <p className="text-lg font-bold">${price.toFixed(2)}</p>
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
    <div className="bg-gray-900/80 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
        <Globe className="w-4 h-4 text-council-purple" /> {name}
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-gray-500 mb-1 flex items-center gap-1"><Waves className="w-3 h-3" /> Earthquakes (30d)</p>
          <p className="text-lg font-bold text-risk-red">{quakes.length}</p>
          {quakes.slice(0, 2).map((q, i) => (
            <p key={i} className="text-xs text-gray-400">M{Number(q.magnitude).toFixed(1)} — {String(q.place || '').slice(0, 30)}</p>
          ))}
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1 flex items-center gap-1"><Thermometer className="w-3 h-3" /> Today's Weather</p>
          {today ? (
            <>
              <p className="text-sm">{Number(today.temp_max).toFixed(0)}°C / {Number(today.temp_min).toFixed(0)}°C</p>
              <p className="text-xs text-gray-400">🌧 {Number(today.precipitation || 0).toFixed(1)}mm</p>
            </>
          ) : <p className="text-xs text-gray-500">No data</p>}
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const ticker = useMarketTicker()
  const risk = useRiskDashboard()

  const stocks = (ticker.data?.stocks || []) as Array<Record<string, unknown>>
  const forex = (ticker.data?.forex || {}) as Record<string, unknown>
  const commodities = (ticker.data?.commodities || []) as Array<Record<string, unknown>>
  const regions = (risk.data?.regions || []) as Array<Record<string, unknown>>
  const disasters = (risk.data?.global_disasters?.alerts || []) as Array<Record<string, unknown>>

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-supply-blue to-council-purple bg-clip-text text-transparent">
          Supply Chain Command Center
        </h1>
        <p className="text-gray-400 mt-1">Real-time market data, risk monitoring & council insights</p>
      </div>

      {/* Market Ticker Bar */}
      <div className="mb-6 bg-gray-900/50 rounded-lg border border-gray-800 p-3">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-4 h-4 text-supply-blue" />
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Live Market Ticker</span>
          {ticker.isFetching && <span className="text-xs text-supply-blue animate-pulse">Updating...</span>}
        </div>
        <div className="flex gap-3 overflow-x-auto pb-1">
          {ticker.isLoading ? (
            <LoadingSkeleton variant="card" count={4} />
          ) : stocks.map((s, i) => <StockCard key={i} stock={s} />)}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Forex */}
        <div>
          {ticker.isLoading ? <LoadingSkeleton variant="card" /> : <ForexCard forex={forex} />}
        </div>

        {/* Commodities */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900/80 rounded-lg p-4 border border-gray-800">
            <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-supply-blue" /> Commodity Prices
            </h3>
            <div className="space-y-2">
              {ticker.isLoading ? <LoadingSkeleton variant="card" count={2} /> :
                commodities.map((c, i) => <CommodityCard key={i} commodity={c} />)}
            </div>
          </div>
        </div>
      </div>

      {/* Risk Dashboard */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-risk-red" /> Supply Chain Risk Monitor
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {risk.isLoading ? <LoadingSkeleton variant="card" count={3} /> :
            regions.map((r, i) => <EarthquakeAlert key={i} region={r} />)}
        </div>
      </div>

      {/* Global Disaster Alerts */}
      {disasters.length > 0 && (
        <div className="bg-gray-900/80 rounded-lg p-4 border border-risk-red/30 mb-6">
          <h3 className="text-sm font-semibold text-risk-red mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> Global Disaster Alerts (GDACS)
          </h3>
          <div className="space-y-2">
            {disasters.slice(0, 5).map((d, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-gray-300">{String(d.title || '')}</span>
                <span className="text-xs text-gray-500">{String(d.date || '')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'MCP Tools', value: '99', icon: Activity, color: 'text-supply-blue' },
          { label: 'Live APIs', value: '26', icon: Globe, color: 'text-green-400' },
          { label: 'Risk Regions', value: String(regions.length || 3), icon: Shield, color: 'text-risk-red' },
          { label: 'Data Sources', value: '40+', icon: TrendingUp, color: 'text-council-purple' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">{label}</span>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <p className="text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
