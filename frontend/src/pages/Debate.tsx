import { useState } from 'react'
import { Flame, ArrowRight } from 'lucide-react'
import { useCouncilQuery } from '@/hooks/useCouncilQuery'
import MarkdownRenderer from '@/components/shared/MarkdownRenderer'
import LoadingSkeleton from '@/components/shared/LoadingSkeleton'

export default function Debate() {
  const [query, setQuery] = useState('')
  const mutation = useCouncilQuery()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    mutation.mutate(query.trim())
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Flame className="w-6 h-6 text-council-purple" />
          Council Debate
        </h1>
        <p className="text-gray-400 text-sm">Full multi-round debate with all agents</p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a supply chain question for full debate..."
          className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-council-purple"
        />
        <button
          type="submit"
          disabled={mutation.isPending || !query.trim()}
          className="px-4 py-3 bg-council-purple rounded-lg text-white hover:bg-council-purple-dark transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          <ArrowRight className="w-5 h-5" />
          Debate
        </button>
      </form>

      {mutation.isPending && <LoadingSkeleton variant="card" count={4} />}

      {mutation.data && (
        <div className="space-y-4">
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
            <h2 className="text-lg font-semibold text-council-purple mb-2">Recommendation</h2>
            <MarkdownRenderer content={mutation.data.recommendation || 'No recommendation'} />
            {mutation.data.confidence != null && (
              <p className="text-sm text-gray-400 mt-2">Confidence: {(mutation.data.confidence * 100).toFixed(0)}%</p>
            )}
          </div>

          {mutation.data.agent_outputs?.map((ao: { agent?: string; name?: string; output?: string; content?: string }, i: number) => (
            <div key={i} className="bg-gray-900 rounded-lg border border-gray-800 p-4">
              <h3 className="text-sm font-semibold text-supply-blue uppercase mb-2">
                {String(ao.agent || ao.name || `Agent ${i + 1}`)}
              </h3>
              <MarkdownRenderer content={String(ao.output || ao.content || '')} />
            </div>
          ))}
        </div>
      )}

      {mutation.isError && (
        <div className="bg-risk-red/10 border border-risk-red/30 rounded-lg p-4 text-risk-red">
          Error: {String(mutation.error)}
        </div>
      )}
    </div>
  )
}
