import { useState } from 'react'
import { Wrench, Search, ChevronDown, ChevronRight, Play, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'
import { useMCPManifest, useMCPInvoke } from '@/hooks/useMCPTools'
import { COUNCIL_AGENTS } from '@/types/council'
import type { MCPTool } from '@/types/mcp'

const CATEGORY_COLORS: Record<string, string> = {
  financial: '#059669',
  commodity: '#d97706',
  forex: '#0891b2',
  news: '#6366f1',
  geopolitical: '#ef4444',
  economic: '#7c3aed',
  disaster: '#dc2626',
  weather: '#0ea5e9',
  climate: '#06b6d4',
  cyber: '#f97316',
  knowledge: '#8b5cf6',
  trade: '#10b981',
  logistics: '#0891b2',
  rag: '#a855f7',
  general: '#6b7280',
}

function HealthBadge({ health }: { health?: MCPTool['health'] }) {
  if (!health || health.calls === 0) {
    return <span className="text-[10px] text-gray-400 font-medium">No calls yet</span>
  }
  const rate = health.success_rate * 100
  const color = rate >= 90 ? 'text-emerald-600' : rate >= 70 ? 'text-amber-600' : 'text-red-600'
  return (
    <div className="flex items-center gap-2">
      <span className={`text-[11px] font-bold ${color}`}>{rate.toFixed(0)}%</span>
      <span className="text-[10px] text-gray-400">{health.calls} calls</span>
      <span className="text-[10px] text-gray-400">{health.avg_latency_ms}ms avg</span>
      {health.last_error && (
        <span className="text-[10px] text-red-500 truncate max-w-[120px]" title={health.last_error}>
          <AlertCircle className="w-3 h-3 inline" /> {health.last_error}
        </span>
      )}
    </div>
  )
}

function ToolCard({ tool, onInvoke }: { tool: MCPTool; onInvoke: (tool: MCPTool) => void }) {
  const [expanded, setExpanded] = useState(false)
  const catColor = CATEGORY_COLORS[tool.category] || '#6b7280'

  return (
    <div className="border border-gray-200 rounded-xl bg-white transition-all hover:shadow-md">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left"
      >
        <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: catColor }} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-gray-900 truncate">{tool.name}</span>
            <span
              className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
              style={{ backgroundColor: `${catColor}15`, color: catColor }}
            >
              {tool.category}
            </span>
          </div>
          <p className="text-xs text-gray-500 truncate mt-0.5">{tool.description}</p>
        </div>
        <HealthBadge health={tool.health} />
        <span className="shrink-0 text-gray-400">
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-100 pt-3">
          {/* Input Schema */}
          <div>
            <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">Input Schema</h4>
            <div className="bg-gray-50 rounded-lg p-3 text-xs font-mono overflow-x-auto">
              {Object.entries(tool.input_schema.properties || {}).map(([key, prop]) => (
                <div key={key} className="flex items-center gap-2 py-0.5">
                  <span className="font-semibold text-gray-700">{key}</span>
                  <span className="text-gray-400">({prop.type})</span>
                  {tool.input_schema.required?.includes(key) && (
                    <span className="text-[9px] bg-red-100 text-red-600 px-1.5 py-0.5 rounded font-bold">required</span>
                  )}
                  {prop.description && <span className="text-gray-500">— {prop.description}</span>}
                </div>
              ))}
              {Object.keys(tool.input_schema.properties || {}).length === 0 && (
                <span className="text-gray-400">No parameters</span>
              )}
            </div>
          </div>

          {/* Allowed Agents */}
          {tool.allowed_agents && tool.allowed_agents.length > 0 && (
            <div>
              <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">Allowed Agents</h4>
              <div className="flex flex-wrap gap-1.5">
                {tool.allowed_agents.map((a) => {
                  const agent = COUNCIL_AGENTS.find((c) => c.key === a)
                  return (
                    <span
                      key={a}
                      className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                      style={{
                        backgroundColor: agent ? `${agent.hexColor}15` : '#f3f4f6',
                        color: agent?.hexColor || '#6b7280',
                      }}
                    >
                      {agent?.label || a}
                    </span>
                  )
                })}
              </div>
            </div>
          )}

          {/* Invoke Button */}
          <button
            onClick={(e) => { e.stopPropagation(); onInvoke(tool) }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            Invoke Tool
          </button>
        </div>
      )}
    </div>
  )
}

function InvokeModal({ tool, onClose }: { tool: MCPTool; onClose: () => void }) {
  const invoke = useMCPInvoke()
  const [params, setParams] = useState<Record<string, unknown>>({})

  const handleInvoke = async () => {
    await invoke.mutateAsync({ tool: tool.name, params })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900">Invoke: {tool.name}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <p className="text-sm text-gray-500">{tool.description}</p>

        <div className="space-y-2">
          {Object.entries(tool.input_schema.properties || {}).map(([key, prop]) => (
            <div key={key}>
              <label className="text-xs font-semibold text-gray-700">
                {key} <span className="text-gray-400">({prop.type})</span>
                {tool.input_schema.required?.includes(key) && <span className="text-red-500"> *</span>}
              </label>
              <input
                type="text"
                placeholder={prop.description || key}
                className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                onChange={(e) => setParams((p) => ({ ...p, [key]: e.target.value }))}
              />
            </div>
          ))}
        </div>

        {invoke.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">
            {String(invoke.error)}
          </div>
        )}

        {invoke.isSuccess && invoke.data && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-bold text-emerald-700">Success ({invoke.data.latency_ms}ms)</span>
            </div>
            <pre className="text-[11px] text-gray-700 overflow-x-auto max-h-40 overflow-y-auto">
              {JSON.stringify(invoke.data.result, null, 2)}
            </pre>
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
          <button
            onClick={handleInvoke}
            disabled={invoke.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg disabled:opacity-50"
          >
            {invoke.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Run
          </button>
        </div>
      </div>
    </div>
  )
}

export default function MCPExplorer() {
  const { data: manifest, isLoading, error } = useMCPManifest()
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [invokeTool, setInvokeTool] = useState<MCPTool | null>(null)

  const tools = manifest?.tools || []
  const categories = manifest?.categories || []

  const filtered = tools.filter((t) => {
    const matchesSearch = !search || t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = !selectedCategory || t.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Wrench className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-gray-900">MCP Explorer</h1>
            <p className="text-sm text-gray-500">{tools.length} tools across {categories.length} categories</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tools..."
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white"
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              !selectedCategory ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat === selectedCategory ? null : cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                selectedCategory === cat ? 'text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
              style={selectedCategory === cat ? { backgroundColor: CATEGORY_COLORS[cat] || '#6b7280' } : {}}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Tool List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <span className="ml-3 text-gray-500">Loading MCP tools...</span>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="w-5 h-5 inline mr-2" />
          Failed to load MCP manifest. Make sure the backend is running.
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <Wrench className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No tools match your search.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {filtered.map((tool) => (
            <ToolCard key={tool.name} tool={tool} onInvoke={setInvokeTool} />
          ))}
        </div>
      )}

      {/* Invoke Modal */}
      {invokeTool && <InvokeModal tool={invokeTool} onClose={() => setInvokeTool(null)} />}
    </div>
  )
}
