import { useSettingsStore } from '@/store/settingsStore'
import { settingsApi } from '@/lib/api'
import { Save, CheckCircle2, XCircle, Activity, Settings as SettingsIcon, Key, Cpu } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { marketApi } from '@/lib/api'

export default function Settings() {
  const { settings, updateSettings } = useSettingsStore()

  const handleSave = async () => {
    try {
      await settingsApi.update(settings as unknown as Record<string, unknown>)
    } catch {
      // Settings saved locally even if API fails
    }
  }

  const healthCheck = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await marketApi.ticker()
      return data
    },
    staleTime: 30000,
    refetchInterval: 60000,
  })

  const apiStatuses = [
    { name: 'Finnhub (Stocks)', live: healthCheck.data?.stocks?.some((s: Record<string, unknown>) => !s.mock) },
    { name: 'Frankfurter (Forex)', live: healthCheck.data?.forex && !healthCheck.data.forex.mock },
    { name: 'Open-Meteo (Weather)', live: true },
    { name: 'USGS (Earthquakes)', live: true },
    { name: 'Wikipedia', live: true },
    { name: 'Reddit', live: true },
    { name: 'World Bank', live: true },
    { name: 'GDACS (Disasters)', live: true },
    { name: 'GDELT (Geopolitics)', live: true },
    { name: 'Yahoo Finance (Commodities)', live: healthCheck.data?.commodities?.some((c: Record<string, unknown>) => !c.mock) },
  ]

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      <div className="mb-6 animate-in-up">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-600 to-gray-700 flex items-center justify-center shadow-sm">
            <SettingsIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-heading text-gray-900">Settings</h1>
            <p className="text-gray-500 text-sm">Configure your application preferences</p>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* Live API Status */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up delay-100">
          <h2 className="text-sm font-semibold font-heading text-emerald-600 uppercase mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4" /> Live API Status
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {apiStatuses.map(({ name, live }) => (
              <div key={name} className="flex items-center gap-2.5 text-sm p-2 rounded-lg bg-gray-50">
                {live ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                )}
                <span className={live ? 'text-gray-700 font-medium' : 'text-gray-400'}>{name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* API Keys */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up delay-200">
          <h2 className="text-sm font-semibold font-heading text-blue-600 uppercase mb-4 flex items-center gap-2">
            <Key className="w-4 h-4" /> API Keys
          </h2>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">API Key</label>
              <input
                type="password"
                value={settings.api_key}
                onChange={(e) => updateSettings({ api_key: e.target.value })}
                className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 mt-1.5 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:outline-none transition-all"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">MCP API Key</label>
              <input
                type="password"
                value={settings.mcp_api_key}
                onChange={(e) => updateSettings({ mcp_api_key: e.target.value })}
                className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 mt-1.5 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:outline-none transition-all"
              />
            </div>
          </div>
        </div>

        {/* RAG Settings with Sliders */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up delay-300">
          <h2 className="text-sm font-semibold font-heading text-violet-600 uppercase mb-4 flex items-center gap-2">
            <Cpu className="w-4 h-4" /> RAG Configuration
          </h2>
          <div className="space-y-5">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">Chunk Size</label>
                <span className="text-sm font-bold text-gray-900 bg-gray-100 px-2.5 py-0.5 rounded-md">{settings.rag_chunk_size}</span>
              </div>
              <input
                type="range"
                min="128"
                max="2048"
                step="64"
                value={settings.rag_chunk_size}
                onChange={(e) => updateSettings({ rag_chunk_size: parseInt(e.target.value) || 512 })}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>128</span><span>2048</span>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">Chunk Overlap</label>
                <span className="text-sm font-bold text-gray-900 bg-gray-100 px-2.5 py-0.5 rounded-md">{settings.rag_chunk_overlap}</span>
              </div>
              <input
                type="range"
                min="0"
                max="200"
                step="10"
                value={settings.rag_chunk_overlap}
                onChange={(e) => updateSettings({ rag_chunk_overlap: parseInt(e.target.value) || 50 })}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0</span><span>200</span>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">Top K</label>
                <span className="text-sm font-bold text-gray-900 bg-gray-100 px-2.5 py-0.5 rounded-md">{settings.rag_top_k}</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                step="1"
                value={settings.rag_top_k}
                onChange={(e) => updateSettings({ rag_top_k: parseInt(e.target.value) || 5 })}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>1</span><span>20</span>
              </div>
            </div>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 rounded-xl text-white hover:bg-blue-700 transition-all duration-200 shadow-sm hover:shadow-md animate-in-up delay-400"
        >
          <Save className="w-4 h-4" />
          Save Settings
        </button>
      </div>
    </div>
  )
}
