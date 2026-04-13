import { useState } from 'react'
import { Flame, ArrowRight, StopCircle, Download } from 'lucide-react'
import { useCouncilStream } from '@/hooks/useCouncilStream'
import MarkdownRenderer from '@/components/shared/MarkdownRenderer'
import ConfidenceBar from '@/components/shared/ConfidenceBar'
import { councilApi } from '@/lib/api'

const AGENT_COLORS: Record<string, string> = {
  risk: 'text-risk-red',
  supply: 'text-supply-blue',
  logistics: 'text-yellow-400',
  market: 'text-council-purple',
  finance: 'text-success-green',
  brand: 'text-pink-400',
  moderator: 'text-council-purple',
}

const AGENT_LABELS: Record<string, string> = {
  risk: 'Risk Sentinel',
  supply: 'Supply Optimizer',
  logistics: 'Logistics Navigator',
  market: 'Market Intelligence',
  finance: 'Finance Guardian',
  brand: 'Brand Protector',
  moderator: 'Council Moderator',
}

export default function Debate() {
  const [query, setQuery] = useState('')
  const { startStream, stopStream, isStreaming, agentOutputs, currentSession } = useCouncilStream()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isStreaming) return
    startStream(query.trim())
  }

  const handleExport = async () => {
    if (!currentSession?.session_id) return
    try {
      const { data } = await councilApi.exportPdf(currentSession.session_id)
      const url = URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = url
      a.download = `debate_${currentSession.session_id.slice(0, 8)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // handle error
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Flame className="w-6 h-6 text-council-purple" />
          Council Debate
        </h1>
        <p className="text-gray-400 text-sm">Full multi-round debate with all agents — streaming in real-time</p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a supply chain question for full debate..."
          className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-council-purple"
          disabled={isStreaming}
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={stopStream}
            className="px-4 py-3 bg-risk-red rounded-lg text-white hover:bg-red-600 transition-colors flex items-center gap-2"
          >
            <StopCircle className="w-5 h-5" />
            Stop
          </button>
        ) : (
          <button
            type="submit"
            disabled={!query.trim()}
            className="px-4 py-3 bg-council-purple rounded-lg text-white hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <ArrowRight className="w-5 h-5" />
            Debate
          </button>
        )}
        {currentSession?.session_id && !isStreaming && (
          <button
            type="button"
            onClick={handleExport}
            className="px-4 py-3 bg-gray-800 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors"
            title="Export PDF"
          >
            <Download className="w-5 h-5" />
          </button>
        )}
      </form>

      {/* Streaming Agent Outputs */}
      <div className="space-y-4">
        {Object.entries(agentOutputs).map(([agent, output]) => (
          <div key={agent} className="bg-gray-900 rounded-lg border border-gray-800 p-4 animate-fade-in">
            <div className="flex items-center justify-between mb-2">
              <h3 className={`font-semibold text-sm uppercase ${AGENT_COLORS[agent] || 'text-gray-300'}`}>
                {AGENT_LABELS[agent] || agent}
              </h3>
              {agent === 'moderator' && currentSession?.confidence != null && (
                <ConfidenceBar value={currentSession.confidence} size="sm" />
              )}
            </div>
            <MarkdownRenderer content={output} />
          </div>
        ))}

        {isStreaming && !Object.keys(agentOutputs).length && (
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-1/3 mb-3" />
            <div className="h-3 bg-gray-700 rounded w-full mb-2" />
            <div className="h-3 bg-gray-700 rounded w-5/6" />
          </div>
        )}
      </div>
    </div>
  )
}
