import { useState } from 'react'
import { Send, StopCircle, Download } from 'lucide-react'
import { useCouncilStream } from '@/hooks/useCouncilStream'
import { councilApi } from '@/lib/api'
import MarkdownRenderer from '@/components/shared/MarkdownRenderer'
import ConfidenceBar from '@/components/shared/ConfidenceBar'
import LoadingSkeleton from '@/components/shared/LoadingSkeleton'

const AGENT_COLORS: Record<string, string> = {
  risk: 'text-risk-red',
  supply: 'text-supply-blue',
  logistics: 'text-yellow-400',
  market: 'text-council-purple',
  finance: 'text-success-green',
  brand: 'text-pink-400',
  moderator: 'text-council-purple',
}

export default function Chat() {
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
      a.download = `council_${currentSession.session_id.slice(0, 8)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // handle error
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex flex-col h-[calc(100vh-4rem)]">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Council Chat</h1>
        <p className="text-gray-400 text-sm">Ask the multi-agent council for supply chain analysis</p>
      </div>

      {/* Agent outputs */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {Object.entries(agentOutputs).map(([agent, output]) => (
          <div key={agent} className="bg-gray-900 rounded-lg border border-gray-800 p-4 animate-fade-in">
            <div className="flex items-center justify-between mb-2">
              <h3 className={`font-semibold text-sm uppercase ${AGENT_COLORS[agent] || 'text-gray-300'}`}>
                {agent}
              </h3>
              {currentSession?.confidence != null && agent === 'moderator' && (
                <ConfidenceBar value={currentSession.confidence} size="sm" />
              )}
            </div>
            <MarkdownRenderer content={output} />
          </div>
        ))}

        {isStreaming && !Object.keys(agentOutputs).length && (
          <LoadingSkeleton variant="message" count={3} />
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about supply chain risks, disruptions, optimizations..."
          className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-supply-blue focus:border-transparent"
          disabled={isStreaming}
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={stopStream}
            className="px-4 py-3 bg-risk-red rounded-lg text-white hover:bg-risk-red-dark transition-colors"
          >
            <StopCircle className="w-5 h-5" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!query.trim()}
            className="px-4 py-3 bg-supply-blue rounded-lg text-white hover:bg-supply-blue-dark transition-colors disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
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
    </div>
  )
}
