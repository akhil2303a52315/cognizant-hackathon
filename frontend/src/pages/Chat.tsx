import { useState } from 'react'
import { Send, StopCircle, Sparkles, ShieldCheck, Loader2, ChevronLeft, Check, Zap, Crown, Database, Globe, Cpu, BookOpen } from 'lucide-react'
import { useCouncilV2Stream } from '@/hooks/useCouncilV2Stream'
import { useCouncilV2Store } from '@/store/councilV2Store'
import type { PipelineStageKey, PipelineStageState } from '@/store/councilV2Store'
import { COUNCIL_AGENTS } from '@/types/council'
import type { AgentInfo, AgentStatus, ModeratorResult } from '@/types/council'
import MarkdownRenderer from '@/components/shared/MarkdownRenderer'
import CitedMarkdownRenderer from '@/components/shared/CitedMarkdownRenderer'

// ── Pipeline Stage Panel ──────────────────────────────────────────────────────
const STAGE_CONFIG: Record<PipelineStageKey, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  rag_fetching: {
    label: 'RAG Retrieval',
    icon: <Database className="w-3.5 h-3.5" />,
    color: '#7c3aed',
    bg: 'rgba(124,58,237,0.1)',
  },
  api_called: {
    label: 'Live APIs',
    icon: <Globe className="w-3.5 h-3.5" />,
    color: '#0ea5e9',
    bg: 'rgba(14,165,233,0.1)',
  },
  mcp_fetched: {
    label: 'Web Scraping',
    icon: <Cpu className="w-3.5 h-3.5" />,
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.1)',
  },
  sources_ready: {
    label: 'Sources Ready',
    icon: <BookOpen className="w-3.5 h-3.5" />,
    color: '#10b981',
    bg: 'rgba(16,185,129,0.1)',
  },
}

const STAGE_ORDER: PipelineStageKey[] = ['rag_fetching', 'api_called', 'mcp_fetched', 'sources_ready']

function PipelinePanel({ stages }: { stages: Record<PipelineStageKey, PipelineStageState> }) {
  const anyActive = STAGE_ORDER.some((k) => stages[k].status !== 'idle')
  if (!anyActive) return null

  return (
    <div
      className="mb-5 px-5 py-3.5 rounded-2xl border backdrop-blur-xl"
      style={{
        background: 'rgba(255,255,255,0.7)',
        borderColor: 'rgba(148,163,184,0.25)',
        boxShadow: '0 2px 16px rgba(0,0,0,0.06)',
      }}
    >
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-3">
        Research Pipeline
      </p>
      <div className="flex items-center gap-2 flex-wrap">
        {STAGE_ORDER.map((key, idx) => {
          const cfg = STAGE_CONFIG[key]
          const st = stages[key]
          const isActive = st.status === 'active'
          const isDone = st.status === 'done'
          const isIdle = st.status === 'idle'

          return (
            <div key={key} className="flex items-center gap-1.5">
              <div
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-bold transition-all duration-500"
                style={{
                  background: isDone ? cfg.bg : isActive ? cfg.bg : 'rgba(148,163,184,0.1)',
                  color: isDone ? cfg.color : isActive ? cfg.color : '#94a3b8',
                  border: `1px solid ${isDone ? cfg.color + '40' : isActive ? cfg.color + '60' : 'transparent'}`,
                  boxShadow: isActive ? `0 0 12px ${cfg.color}30` : 'none',
                  opacity: isIdle ? 0.5 : 1,
                }}
              >
                <span
                  className={isActive ? 'animate-pulse' : ''}
                  style={{ color: isDone || isActive ? cfg.color : '#94a3b8' }}
                >
                  {isDone ? <Check className="w-3.5 h-3.5" /> : cfg.icon}
                </span>
                <span>{cfg.label}</span>
                {isActive && (
                  <span className="ml-0.5">
                    <Loader2 className="w-3 h-3 animate-spin" style={{ color: cfg.color }} />
                  </span>
                )}
                {isDone && key === 'sources_ready' && st.count > 0 && (
                  <span
                    className="ml-1 px-1.5 py-0.5 rounded-full text-[9px] font-black text-white"
                    style={{ background: cfg.color }}
                  >
                    {st.count}
                  </span>
                )}
              </div>
              {idx < STAGE_ORDER.length - 1 && (
                <span
                  className="text-slate-200 text-xs font-light transition-colors duration-300"
                  style={{ color: isDone ? cfg.color + '80' : '#e2e8f0' }}
                >
                  →
                </span>
              )}
            </div>
          )
        })}
      </div>
      {STAGE_ORDER.map((key) => {
        const st = stages[key]
        if (st.status === 'active' && st.detail) {
          return (
            <p key={key} className="mt-2 text-[10px] text-slate-400 italic animate-pulse">
              {st.detail}
            </p>
          )
        }
        return null
      })}
    </div>
  )
}

// ── Status Indicator ──────────────────────────────────────────────────────────
function StatusIndicator({ status, color }: { status: AgentStatus; color: string }) {
  if (status === 'thinking') {
    return (
      <span className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: color }} />
        <span className="text-[11px] font-medium" style={{ color }}>Thinking...</span>
      </span>
    )
  }
  if (status === 'done') return <Check className="w-3.5 h-3.5 text-emerald-500" />
  if (status === 'error') return <span className="w-2 h-2 rounded-full bg-red-500" />
  return <span className="w-2 h-2 rounded-full bg-gray-300" />
}

// ── Agent Tab ─────────────────────────────────────────────────────────────────
function AgentTab({
  agent, isOpen, onClick, roundState,
}: {
  agent: AgentInfo; isOpen: boolean; onClick: () => void
  roundState: { status: AgentStatus; confidence: number }
}) {
  const isActive = isOpen || roundState.status === 'thinking' || roundState.status === 'done'
  return (
    <button
      onClick={onClick}
      className="w-[160px] h-12 flex items-center gap-2 px-3 rounded-l-xl text-left transition-all duration-300 border border-r-0"
      style={{
        backgroundColor: isOpen ? `${agent.hexColor}14` : roundState.status === 'thinking' ? `${agent.hexColor}08` : 'white',
        borderColor: isActive ? `${agent.hexColor}40` : '#e5e7eb',
        borderLeftWidth: '3px',
        borderLeftColor: isOpen ? agent.hexColor : isActive ? `${agent.hexColor}60` : '#e5e7eb',
      }}
    >
      <span className="shrink-0 transition-transform duration-300"
        style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', color: isActive ? agent.hexColor : '#9ca3af' }}>
        <ChevronLeft className="w-4 h-4" />
      </span>
      <span className="flex-1 text-[14px] font-semibold font-heading truncate transition-colors duration-200"
        style={{ color: isActive ? agent.hexColor : '#1f2937' }}>
        {agent.label}
      </span>
      <StatusIndicator status={roundState.status} color={agent.hexColor} />
    </button>
  )
}

// ── Moderator Panel ───────────────────────────────────────────────────────────
function ModeratorPanel({ result, roundLabel }: { result: ModeratorResult; roundLabel: string }) {
  return (
    <div className="space-y-6 animate-in-up p-8 rounded-[2.5rem] relative overflow-hidden backdrop-blur-3xl"
      style={{
        background: 'linear-gradient(135deg, rgba(255,255,255,0.85) 0%, rgba(139, 92, 246, 0.08) 100%)',
        border: '2px solid rgba(139, 92, 246, 0.4)',
        boxShadow: '0 0 35px rgba(139, 92, 246, 0.25), inset 0 0 20px rgba(139, 92, 246, 0.1)',
      }}>
      <div className="absolute -bottom-20 -right-20 w-[400px] h-[400px] rounded-full bg-violet-400/20 blur-[80px] pointer-events-none mix-blend-multiply" />
      <div className="relative z-10 flex items-center gap-5 mb-8">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.5)]">
          <Crown className="w-7 h-7 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-black text-gray-900 font-outfit">Moderator Summary</h2>
          <p className="text-xs text-violet-600/80 font-bold uppercase tracking-widest mt-0.5">{roundLabel}</p>
        </div>
        <div className="ml-auto px-5 py-2.5 rounded-2xl bg-white/60 border border-violet-200/50 flex flex-col items-center backdrop-blur-sm shadow-sm gap-0.5">
          <span className="text-[9px] text-violet-500 font-black uppercase tracking-tighter">Consensus</span>
          <span className="text-xl font-black text-violet-600 font-outfit leading-none">{result.consensus}%</span>
        </div>
      </div>
      <div className="relative z-10 space-y-3 bg-white/40 p-6 rounded-3xl border border-white/60 backdrop-blur-md">
        {COUNCIL_AGENTS.map((agent) => {
          const score = result.scores[agent.key] || 0
          return (
            <div key={agent.key} className="flex items-center gap-4">
              <span className="w-2.5 h-2.5 rounded-full shrink-0 shadow-sm" style={{ backgroundColor: agent.hexColor }} />
              <span className="text-sm font-bold w-24 truncate font-outfit" style={{ color: agent.hexColor }}>{agent.label}</span>
              <div className="flex-1 h-2.5 bg-gray-200/50 rounded-full overflow-hidden shadow-inner">
                <div className="h-full rounded-full transition-all duration-700 shadow-[0_0_10px_rgba(0,0,0,0.1)]"
                  style={{ width: `${score}%`, backgroundColor: agent.hexColor }} />
              </div>
              <span className="text-sm font-black font-outfit w-12 text-right" style={{ color: agent.hexColor }}>{score}%</span>
            </div>
          )
        })}
      </div>
      {result.summary && (
        <div className="relative z-10 mt-6 p-6 bg-white/50 rounded-3xl border border-white/60 backdrop-blur-md shadow-inner">
          <div className="prose prose-violet max-w-none text-gray-800 font-inter font-medium leading-relaxed prose-headings:font-outfit prose-headings:font-black prose-strong:font-bold">
            <MarkdownRenderer content={result.summary} />
          </div>
        </div>
      )}
    </div>
  )
}

// ── Supervisor Panel ──────────────────────────────────────────────────────────
function SupervisorPanel({ output, confidence }: { output: string; confidence: number }) {
  return (
    <div className="space-y-6 animate-in-up p-8 rounded-[2.5rem] relative overflow-hidden backdrop-blur-3xl"
      style={{
        background: 'linear-gradient(135deg, rgba(255,255,255,0.85) 0%, rgba(16, 185, 129, 0.08) 100%)',
        border: '2px solid rgba(16, 185, 129, 0.4)',
        boxShadow: '0 0 35px rgba(16, 185, 129, 0.25), inset 0 0 20px rgba(16, 185, 129, 0.1)',
      }}>
      <div className="absolute -bottom-20 -right-20 w-[400px] h-[400px] rounded-full bg-emerald-400/20 blur-[80px] pointer-events-none mix-blend-multiply" />
      <div className="relative z-10 flex items-center gap-5 mb-8">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.5)]">
          <ShieldCheck className="w-7 h-7 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-black text-gray-900 font-outfit">Supervisor — Final Verdict</h2>
          <p className="text-xs text-emerald-600/80 font-bold uppercase tracking-widest mt-0.5">Round 3: Supervisor Review</p>
        </div>
        <div className="ml-auto px-5 py-2.5 rounded-2xl bg-white/60 border border-emerald-200/50 flex flex-col items-center backdrop-blur-sm shadow-sm gap-0.5">
          <span className="text-[9px] text-emerald-500 font-black uppercase tracking-tighter">Confidence</span>
          <span className="text-xl font-black text-emerald-600 font-outfit leading-none">{confidence}%</span>
        </div>
      </div>
      <div className="relative z-10 p-8 bg-white/40 rounded-3xl border border-white/60 backdrop-blur-md shadow-inner">
        <div className="prose prose-emerald max-w-none text-gray-800 font-inter text-[16px] leading-relaxed prose-headings:font-outfit prose-headings:font-black prose-strong:font-bold prose-strong:text-emerald-900">
          <MarkdownRenderer content={output} />
        </div>
      </div>
    </div>
  )
}

// ── Main Chat Component ───────────────────────────────────────────────────────
export default function Chat() {
  const [query, setQuery] = useState('')
  const { startStream, stopStream } = useCouncilV2Stream()
  const store = useCouncilV2Store()
  const isStreaming = store.isStreaming

  const {
    currentRound, agents, moderatorR1, moderatorR2, supervisorResult,
    selectedAgent, viewMode, streamError, citationMaps, pipelineStages,
  } = store

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isStreaming) return
    startStream(query.trim())
  }

  const activeRoundKey = currentRound <= 1 ? 'round1' : 'round2'
  const selectedAgentInfo = COUNCIL_AGENTS.find((a) => a.key === selectedAgent)
  const selectedAgentState = selectedAgent ? agents[selectedAgent] : null

  const handleTabClick = (agentKey: string) => {
    if (selectedAgent === agentKey && viewMode === 'agent') {
      store.setSelectedAgent('')
    } else {
      store.setSelectedAgent(agentKey)
    }
  }

  const getMainContent = () => {
    if (viewMode === 'supervisor' && supervisorResult) {
      return <SupervisorPanel output={supervisorResult.output} confidence={supervisorResult.confidence} />
    }
    if (viewMode === 'moderator') {
      if (currentRound >= 2 && moderatorR2) return <ModeratorPanel result={moderatorR2} roundLabel="Round 2 Scores" />
      if (moderatorR1) return <ModeratorPanel result={moderatorR1} roundLabel="Round 1 Scores" />
      return (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
          <span className="ml-3 text-gray-500">Moderator is scoring agents...</span>
        </div>
      )
    }
    if (selectedAgent && selectedAgentInfo && selectedAgentState) {
      const roundState = selectedAgentState[activeRoundKey]
      return (
        <div className="animate-in-up">
          <div
            className="rounded-[2.5rem] p-8 lg:p-10 transition-all duration-700 backdrop-blur-3xl relative overflow-hidden group"
            style={{
              background: `linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, ${selectedAgentInfo.hexColor}08 100%)`,
              borderColor: `${selectedAgentInfo.hexColor}60`,
              borderWidth: '2px', borderStyle: 'solid',
              boxShadow: `0 0 35px ${selectedAgentInfo.hexColor}30, inset 0 0 25px ${selectedAgentInfo.hexColor}15`,
            }}
          >
            <div className="absolute -bottom-32 -right-32 w-[600px] h-[600px] rounded-full blur-[120px] opacity-20 pointer-events-none transition-all duration-1000 group-hover:opacity-30 mix-blend-multiply"
              style={{ backgroundColor: selectedAgentInfo.hexColor }} />
            <div className="relative z-10">
              <div className="flex items-center gap-5 mb-8">
                <div className="w-5 h-5 rounded-full shrink-0 shadow-[0_0_20px] animate-pulse relative"
                  style={{ backgroundColor: selectedAgentInfo.hexColor, boxShadow: `0 0 20px ${selectedAgentInfo.hexColor}80` }}>
                  <div className="absolute inset-0 rounded-full animate-ping opacity-30" style={{ backgroundColor: selectedAgentInfo.hexColor }} />
                </div>
                <div>
                  <h3 className="font-black text-2xl text-gray-900 font-outfit tracking-tight">{selectedAgentInfo.label} Agent</h3>
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-[10px] text-gray-400 font-bold tracking-[0.2em] uppercase">
                      Analysis Round {activeRoundKey === 'round1' ? '1' : '2'}
                    </span>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-200" />
                    <span className="text-[11px] font-extrabold uppercase tracking-widest flex items-center gap-2" style={{ color: selectedAgentInfo.hexColor }}>
                      <Zap className="w-3 h-3" />
                      {roundState.status === 'thinking' ? 'Processing...' : 'Verified complete'}
                    </span>
                  </div>
                </div>
                {roundState.confidence > 0 && (
                  <div className="ml-auto px-6 py-2.5 rounded-2xl bg-white/80 border border-white backdrop-blur-md shadow-xl shadow-black/[0.02] flex flex-col items-center">
                    <span className="text-[9px] text-gray-400 font-black uppercase tracking-tighter">Confidence Score</span>
                    <span className="text-xl font-black font-outfit leading-none mt-0.5" style={{ color: selectedAgentInfo.hexColor }}>
                      {roundState.confidence}%
                    </span>
                  </div>
                )}
              </div>

              {roundState.status === 'thinking' && !roundState.output && (
                <div className="flex flex-col items-center justify-center py-24 text-gray-300 gap-5">
                  <div className="relative">
                    <Loader2 className="w-12 h-12 animate-spin text-gray-200" />
                    <div className="absolute inset-0 w-12 h-12 rounded-full border-t-2 border-blue-500 animate-spin" style={{ animationDuration: '0.6s' }} />
                  </div>
                  <span className="text-xs font-black font-outfit uppercase tracking-[0.3em] animate-pulse text-gray-400">Deep Reasoning...</span>
                </div>
              )}

              <div className="text-gray-700 font-inter leading-relaxed text-[17px] font-medium
                             prose prose-blue max-w-none
                             prose-headings:font-outfit prose-headings:text-gray-950 prose-headings:font-black prose-headings:tracking-tight
                             prose-strong:text-gray-950 prose-strong:font-bold prose-strong:font-outfit
                             prose-p:mb-6 prose-li:mb-2
                             prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:bg-blue-50/50 prose-blockquote:p-4 prose-blockquote:rounded-r-xl">
                <CitedMarkdownRenderer
                  content={roundState.output || ''}
                  urlMap={citationMaps[selectedAgent] || {}}
                  accentColor={selectedAgentInfo.hexColor}
                />
              </div>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  const hasStarted = currentRound > 0 || isStreaming

  return (
    <div className="flex flex-col h-[calc(100vh)] bg-slate-50 relative overflow-hidden z-0">
      <div className="absolute top-[-20%] left-[-10%] w-[60vw] h-[60vw] rounded-full bg-blue-300/20 blur-[120px] pointer-events-none -z-10 mix-blend-multiply" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-purple-300/20 blur-[120px] pointer-events-none -z-10 mix-blend-multiply" />

      <div className="flex flex-1 overflow-hidden relative">
        {/* Left: Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
            {streamError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">{streamError}</div>
            )}

            {/* Pipeline animation panel — shown while fetching data */}
            {isStreaming && <PipelinePanel stages={pipelineStages} />}

            {hasStarted ? getMainContent() : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <div className="w-24 h-24 mb-6 rounded-full bg-blue-50/50 backdrop-blur-sm border border-blue-100 flex items-center justify-center shadow-inner">
                  <Sparkles className="w-12 h-12 text-blue-400" />
                </div>
                <p className="text-3xl font-black text-slate-800 font-outfit tracking-tight">Start a Council Debate</p>
                <p className="text-[16px] text-slate-500 font-inter mt-3 max-w-md text-center leading-relaxed">
                  Ask a question to activate 6 AI agents who will automatically analyze, debate, and deliver a final verdict through 3 rigorous rounds.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2 mt-8 max-w-lg">
                  {COUNCIL_AGENTS.map((a) => (
                    <div key={a.key}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/60 backdrop-blur-md border shadow-sm transition-all hover:scale-105"
                      style={{ borderColor: `${a.hexColor}30` }}>
                      <span className="w-2 h-2 rounded-full shadow-sm" style={{ backgroundColor: a.hexColor }} />
                      <span className="text-[11px] font-bold font-outfit tracking-wide uppercase" style={{ color: a.hexColor }}>{a.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="px-4 sm:px-8 py-5 border-t border-gray-200/60 bg-white/60 backdrop-blur-2xl relative z-20">
            <form onSubmit={handleSubmit} className="max-w-4xl mx-auto w-full">
              <div className="relative group">
                <div className="absolute -inset-px bg-gradient-to-r from-blue-500 to-violet-500 rounded-xl opacity-0 group-focus-within:opacity-20 blur transition-opacity duration-500" />
                <div className="relative flex items-center bg-white border border-gray-200 rounded-xl shadow-sm group-focus-within:border-blue-300 group-focus-within:shadow-[0_0_0_3px_rgba(59,130,246,0.1)] transition-all duration-300">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask the council a complex supply chain question..."
                    className="flex-1 bg-transparent px-5 py-3.5 text-[15px] font-medium text-gray-900 placeholder:text-gray-400 placeholder:font-heading focus:outline-none"
                    disabled={isStreaming}
                  />
                  {isStreaming ? (
                    <button type="button" onClick={stopStream}
                      className="shrink-0 mr-2 flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg text-white text-[13px] font-heading font-semibold transition-all duration-200 shadow-sm">
                      <StopCircle className="w-4 h-4" />
                      Stop
                    </button>
                  ) : (
                    <button type="submit" disabled={!query.trim()}
                      className="shrink-0 mr-2 flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 rounded-lg text-white text-[13px] font-heading font-semibold transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm shadow-blue-500/20">
                      <Send className="w-4 h-4" />
                      Run
                    </button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>

        {/* Right: Agent Tabs */}
        {hasStarted && (
          <div className="hidden md:flex flex-col items-end justify-center gap-2 pr-0 pl-2 py-4 z-10">
            {COUNCIL_AGENTS.map((agent) => {
              const state = agents[agent.key]
              if (!state) return null
              const roundState = state[activeRoundKey]
              const isOpen = selectedAgent === agent.key && viewMode === 'agent'
              return (
                <AgentTab key={agent.key} agent={agent} isOpen={isOpen}
                  onClick={() => handleTabClick(agent.key)} roundState={roundState} />
              )
            })}
            {/* Moderator Tab */}
            {(moderatorR1 || (isStreaming && currentRound >= 1)) && (
              <button
                onClick={() => store.setViewMode('moderator')}
                className={`w-[160px] h-12 flex items-center gap-2 px-3 rounded-l-xl text-left transition-all duration-300 border border-r-0 ${viewMode === 'moderator' ? 'bg-violet-50' : 'bg-white'}`}
                style={{ borderColor: viewMode === 'moderator' ? 'rgba(139,92,246,0.4)' : '#e5e7eb', borderLeftWidth: '3px', borderLeftColor: viewMode === 'moderator' ? '#7c3aed' : '#e5e7eb' }}
              >
                <Crown className="w-4 h-4 text-violet-500" />
                <span className="text-[13px] font-semibold text-violet-700">Moderator</span>
              </button>
            )}
            {/* Supervisor Tab */}
            {(supervisorResult || (isStreaming && currentRound >= 3)) && (
              <button
                onClick={() => store.setViewMode('supervisor')}
                className={`w-[160px] h-12 flex items-center gap-2 px-3 rounded-l-xl text-left transition-all duration-300 border border-r-0 ${viewMode === 'supervisor' ? 'bg-emerald-50' : 'bg-white'}`}
                style={{ borderColor: viewMode === 'supervisor' ? 'rgba(16,185,129,0.4)' : '#e5e7eb', borderLeftWidth: '3px', borderLeftColor: viewMode === 'supervisor' ? '#059669' : '#e5e7eb' }}
              >
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span className="text-[13px] font-semibold text-emerald-700">Supervisor</span>
              </button>
            )}
          </div>
        )}

        {/* Mobile: Bottom agent drawer */}
        {hasStarted && (
          <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 shadow-lg">
            <div className="flex overflow-x-auto gap-2 p-2">
              {COUNCIL_AGENTS.map((agent) => {
                const state = agents[agent.key]
                if (!state) return null
                const roundState = state[activeRoundKey]
                const isActive = selectedAgent === agent.key && viewMode === 'agent'
                return (
                  <button key={agent.key} onClick={() => handleTabClick(agent.key)}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap border transition-all duration-200 shrink-0"
                    style={{
                      backgroundColor: isActive ? `${agent.hexColor}14` : 'white',
                      borderColor: isActive ? agent.hexColor : '#e5e7eb',
                      color: isActive ? agent.hexColor : '#1f2937',
                    }}>
                    <StatusIndicator status={roundState.status} color={agent.hexColor} />
                    {agent.label}
                  </button>
                )
              })}
              {(moderatorR1 || (isStreaming && currentRound >= 1)) && (
                <button onClick={() => store.setViewMode('moderator')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap border transition-all duration-200 shrink-0 ${viewMode === 'moderator' ? 'bg-violet-50 border-violet-300 text-violet-700' : 'bg-white border-gray-200 text-gray-700'}`}>
                  <Crown className="w-3 h-3" /> Moderator
                </button>
              )}
              {(supervisorResult || (isStreaming && currentRound >= 3)) && (
                <button onClick={() => store.setViewMode('supervisor')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap border transition-all duration-200 shrink-0 ${viewMode === 'supervisor' ? 'bg-emerald-50 border-emerald-300 text-emerald-700' : 'bg-white border-gray-200 text-gray-700'}`}>
                  <ShieldCheck className="w-3 h-3" /> Supervisor
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
