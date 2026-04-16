import { useState } from 'react'
import { BookOpen, Search, Upload, Loader2, AlertCircle, FileText, Database, BarChart3, Link as LinkIcon } from 'lucide-react'
import { useRAGQuery, useRAGStats, useRAGCollections } from '@/hooks/useRAGQuery'
import { ragApi } from '@/lib/api'
import type { RAGResponse, Citation } from '@/types/rag'

function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  return (
    <div className="border border-gray-200 rounded-xl p-4 bg-white space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-gray-400">#{index + 1}</span>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold text-gray-500">{citation.source}</span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
            {(citation.score * 100).toFixed(1)}%
          </span>
        </div>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed line-clamp-4">{citation.content}</p>
      {citation.metadata && Object.keys(citation.metadata).length > 0 && (
        <div className="text-[10px] text-gray-400 font-mono overflow-x-auto">
          {Object.entries(citation.metadata).map(([k, v]) => (
            <span key={k} className="mr-3">{k}: {String(v)}</span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function RAGExplorer() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<'standard' | 'hybrid' | 'graph'>('hybrid')
  const [topK, setTopK] = useState(5)
  const [result, setResult] = useState<RAGResponse | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)

  const ragMutation = useRAGQuery()
  const { data: stats, isLoading: statsLoading } = useRAGStats()
  const { data: collectionsData, isLoading: collLoading } = useRAGCollections()

  const [uploading, setUploading] = useState(false)
  const [uploadUrl, setUploadUrl] = useState('')
  const [uploadMsg, setUploadMsg] = useState<string | null>(null)

  const handleQuery = async () => {
    if (!query.trim()) return
    setQueryError(null)
    setResult(null)
    try {
      const res = await ragMutation.mutateAsync({ query: query.trim(), mode, topK })
      setResult(res as RAGResponse)
    } catch (err: unknown) {
      setQueryError(err instanceof Error ? err.message : 'Query failed')
    }
  }

  const handleUploadUrl = async () => {
    if (!uploadUrl.trim()) return
    setUploading(true)
    setUploadMsg(null)
    try {
      await ragApi.uploadUrl(uploadUrl.trim())
      setUploadMsg('URL ingested successfully')
      setUploadUrl('')
    } catch {
      setUploadMsg('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const collections = (collectionsData as { collections?: { name: string; document_count?: number }[] })?.collections || []

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
          <BookOpen className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-black text-gray-900">RAG Explorer</h1>
          <p className="text-sm text-gray-500">Query documents, manage collections, explore retrieval</p>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-3">
          <FileText className="w-5 h-5 text-blue-500" />
          <div>
            <p className="text-2xl font-black text-gray-900">{statsLoading ? '...' : (stats as Record<string, number>)?.documents || 0}</p>
            <p className="text-[11px] text-gray-500 font-medium">Documents</p>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-3">
          <Database className="w-5 h-5 text-violet-500" />
          <div>
            <p className="text-2xl font-black text-gray-900">{statsLoading ? '...' : (stats as Record<string, number>)?.collections || 0}</p>
            <p className="text-[11px] text-gray-500 font-medium">Collections</p>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-emerald-500" />
          <div>
            <p className="text-2xl font-black text-gray-900">{statsLoading ? '...' : (stats as Record<string, number>)?.queries || 0}</p>
            <p className="text-[11px] text-gray-500 font-medium">Queries</p>
          </div>
        </div>
      </div>

      {/* Query Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-bold text-gray-900">Query Documents</h2>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
              placeholder="Search documents..."
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
            />
          </div>
          <button
            onClick={handleQuery}
            disabled={ragMutation.isPending || !query.trim()}
            className="px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white text-sm font-semibold rounded-xl disabled:opacity-50 transition-colors"
          >
            {ragMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
          </button>
        </div>

        {/* Mode selector */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-gray-500">Mode:</span>
          {(['standard', 'hybrid', 'graph'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                mode === m ? 'bg-violet-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
          <span className="text-xs text-gray-400 ml-2">Top K:</span>
          <input
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-16 px-2 py-1 border border-gray-200 rounded-lg text-xs text-center"
          />
        </div>

        {/* Error */}
        {queryError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" /> {queryError}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-4 mt-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-700">Answer</h3>
              <div className="flex items-center gap-3 text-[11px] text-gray-500">
                <span>{result.chunks_retrieved} chunks</span>
                <span>{result.latency_ms}ms</span>
                <span className="font-bold text-violet-600">{(result.confidence * 100).toFixed(0)}% confidence</span>
              </div>
            </div>
            <div className="prose prose-violet max-w-none text-sm text-gray-800 bg-gray-50 p-4 rounded-xl border border-gray-100">
              {result.answer}
            </div>

            {result.citations.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-bold text-gray-700">Citations ({result.citations.length})</h3>
                <div className="grid gap-2">
                  {result.citations.map((c, i) => (
                    <CitationCard key={i} citation={c} index={i} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Collections */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
        <h2 className="text-lg font-bold text-gray-900">Collections</h2>
        {collLoading ? (
          <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
        ) : collections.length === 0 ? (
          <p className="text-sm text-gray-400">No collections found. Upload documents to create one.</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {collections.map((c) => (
              <div key={c.name} className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-100">
                <Database className="w-4 h-4 text-violet-500" />
                <span className="text-sm font-semibold text-gray-700">{c.name}</span>
                {c.document_count !== undefined && (
                  <span className="text-[10px] text-gray-400 ml-auto">{c.document_count} docs</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload URL */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
        <h2 className="text-lg font-bold text-gray-900">Ingest URL</h2>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="url"
              value={uploadUrl}
              onChange={(e) => setUploadUrl(e.target.value)}
              placeholder="https://example.com/document"
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
          <button
            onClick={handleUploadUrl}
            disabled={uploading || !uploadUrl.trim()}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl disabled:opacity-50"
          >
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            Ingest
          </button>
        </div>
        {uploadMsg && (
          <p className={`text-xs ${uploadMsg.includes('success') ? 'text-emerald-600' : 'text-red-600'}`}>{uploadMsg}</p>
        )}
      </div>
    </div>
  )
}
