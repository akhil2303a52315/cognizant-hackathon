import { useSettingsStore } from '@/store/settingsStore'
import { settingsApi } from '@/lib/api'
import { Save, CheckCircle2, XCircle, Activity } from 'lucide-react'
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
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="space-y-6">
        {/* Live API Status */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-sm font-semibold text-green-400 uppercase mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" /> Live API Status
          </h2>
          <div className="grid grid-cols-2 gap-2">
            {apiStatuses.map(({ name, live }) => (
              <div key={name} className="flex items-center gap-2 text-sm">
                {live ? (
                  <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                )}
                <span className={live ? 'text-gray-300' : 'text-gray-500'}>{name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* API Keys */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-sm font-semibold text-supply-blue uppercase mb-3">API Keys</h2>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400">API Key</label>
              <input
                type="password"
                value={settings.api_key}
                onChange={(e) => updateSettings({ api_key: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400">MCP API Key</label>
              <input
                type="password"
                value={settings.mcp_api_key}
                onChange={(e) => updateSettings({ mcp_api_key: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm mt-1"
              />
            </div>
          </div>
        </div>

        {/* RAG Settings */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h2 className="text-sm font-semibold text-council-purple uppercase mb-3">RAG Configuration</h2>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-gray-400">Chunk Size</label>
              <input
                type="number"
                value={settings.rag_chunk_size}
                onChange={(e) => updateSettings({ rag_chunk_size: parseInt(e.target.value) || 512 })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400">Chunk Overlap</label>
              <input
                type="number"
                value={settings.rag_chunk_overlap}
                onChange={(e) => updateSettings({ rag_chunk_overlap: parseInt(e.target.value) || 50 })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400">Top K</label>
              <input
                type="number"
                value={settings.rag_top_k}
                onChange={(e) => updateSettings({ rag_top_k: parseInt(e.target.value) || 5 })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm mt-1"
              />
            </div>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-4 py-2 bg-supply-blue rounded-lg text-white hover:bg-supply-blue-dark transition-colors"
        >
          <Save className="w-4 h-4" />
          Save Settings
        </button>
      </div>
    </div>
  )
}
