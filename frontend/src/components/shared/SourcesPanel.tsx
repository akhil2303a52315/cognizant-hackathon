import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, ExternalLink, ChevronDown, ChevronUp, X, Filter } from 'lucide-react'

interface SourceRef {
  num: number
  title: string
  url: string
  agent?: string
  agentColor?: string
}

interface SourcesPanelProps {
  sources: SourceRef[]
  citationMap?: Record<string, string>
  accentColor?: string
  className?: string
}

export default function SourcesPanel({
  sources,
  citationMap = {},
  accentColor = '#6366f1',
  className = '',
}: SourcesPanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [filterAgent, setFilterAgent] = useState<string | null>(null)

  const uniqueAgents = [...new Set(sources.map(s => s.agent).filter(Boolean))]
  const filteredSources = filterAgent
    ? sources.filter(s => s.agent === filterAgent)
    : sources

  const sourceCount = sources.length

  if (sourceCount === 0) return null

  return (
    <div className={`relative ${className}`}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="group flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
        style={{
          background: `linear-gradient(135deg, ${accentColor}15 0%, ${accentColor}08 100%)`,
          border: `1px solid ${accentColor}30`,
          color: accentColor,
        }}
      >
        <BookOpen className="w-4 h-4" />
        <span>{sourceCount} Source{sourceCount !== 1 ? 's' : ''} & References</span>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 ml-1 transition-transform" />
        ) : (
          <ChevronDown className="w-4 h-4 ml-1 transition-transform" />
        )}
        <span
          className="ml-1 px-2 py-0.5 rounded-full text-[10px] font-black"
          style={{
            background: `${accentColor}20`,
            color: accentColor,
          }}
        >
          {sourceCount}
        </span>
      </button>

      {/* Expandable Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -10 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -10 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div
              className="mt-2 rounded-2xl border backdrop-blur-xl overflow-hidden"
              style={{
                background: `linear-gradient(135deg, ${accentColor}05 0%, rgba(255,255,255,0.95) 100%)`,
                borderColor: `${accentColor}20`,
              }}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-3 border-b" style={{ borderColor: `${accentColor}10` }}>
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4" style={{ color: accentColor }} />
                  <span className="text-sm font-bold text-gray-800">References & Sources</span>
                </div>
                <div className="flex items-center gap-2">
                  {/* Agent Filter */}
                  {uniqueAgents.length > 1 && (
                    <div className="flex items-center gap-1">
                      <Filter className="w-3 h-3 text-gray-400" />
                      <select
                        value={filterAgent || ''}
                        onChange={(e) => setFilterAgent(e.target.value || null)}
                        className="text-xs bg-white border border-gray-200 rounded-lg px-2 py-1 text-gray-600 focus:outline-none focus:ring-1 focus:ring-indigo-300"
                      >
                        <option value="">All Agents</option>
                        {uniqueAgents.map(agent => (
                          <option key={agent} value={agent}>{agent}</option>
                        ))}
                      </select>
                    </div>
                  )}
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>

              {/* Sources List */}
              <div className="max-h-[400px] overflow-y-auto p-3 space-y-1.5 scrollbar-thin scrollbar-thumb-gray-200">
                {filteredSources.map((source, index) => (
                  <motion.a
                    key={`${source.agent}-${source.num}-${index}`}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.03 }}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm bg-white/80 border border-gray-100 hover:border-gray-200 hover:shadow-md transition-all duration-200 group"
                    style={{
                      borderLeftColor: source.agentColor || accentColor,
                      borderLeftWidth: '3px',
                    }}
                  >
                    {/* Citation Number Badge */}
                    <span
                      className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-black text-white"
                      style={{ background: source.agentColor || accentColor }}
                    >
                      {source.num}
                    </span>

                    {/* Title */}
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-800 font-medium truncate group-hover:text-gray-900 transition-colors">
                        {source.title}
                      </p>
                      <p className="text-[11px] text-gray-400 truncate mt-0.5">
                        {source.url}
                      </p>
                    </div>

                    {/* Agent Tag */}
                    {source.agent && (
                      <span
                        className="flex-shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                        style={{
                          background: `${source.agentColor || '#666'}15`,
                          color: source.agentColor || '#666',
                        }}
                      >
                        {source.agent}
                      </span>
                    )}

                    {/* External Link Icon */}
                    <ExternalLink className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors flex-shrink-0" />
                  </motion.a>
                ))}

                {/* Citation Map Entries (from backend) */}
                {Object.entries(citationMap).map(([num, url], index) => {
                  if (filteredSources.some(s => s.num === Number(num))) return null
                  if (!url || !url.startsWith('http')) return null
                  return (
                    <motion.a
                      key={`citation-${num}`}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: (filteredSources.length + index) * 0.03 }}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm bg-white/80 border border-gray-100 hover:border-gray-200 hover:shadow-md transition-all duration-200 group"
                      style={{ borderLeftColor: accentColor, borderLeftWidth: '3px' }}
                    >
                      <span
                        className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-black text-white"
                        style={{ background: accentColor }}
                      >
                        {num}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-gray-800 font-medium truncate group-hover:text-gray-900 transition-colors">
                          Source [{num}]
                        </p>
                        <p className="text-[11px] text-gray-400 truncate mt-0.5">{url}</p>
                      </div>
                      <ExternalLink className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors flex-shrink-0" />
                    </motion.a>
                  )
                })}

                {filteredSources.length === 0 && Object.keys(citationMap).length === 0 && (
                  <div className="text-center py-8 text-gray-400 text-sm">
                    No sources available
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="px-5 py-2.5 border-t border-gray-100 flex items-center justify-between">
                <span className="text-[11px] text-gray-400">
                  Click any source to open the original reference
                </span>
                <span className="text-[11px] font-semibold" style={{ color: accentColor }}>
                  {filteredSources.length} of {sourceCount}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
