import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ShieldAlert, GitBranch, Navigation, TrendingUp, DollarSign,
  Megaphone, Crown, RotateCcw, CheckCircle2, Lock, Users, 
  Zap, BarChart3, MessageSquare, ArrowRight, StopCircle
} from "lucide-react"
import { useCouncilStore } from '@/store/councilStore'
import { useCouncilStream } from '@/hooks/useCouncilStream'
import { useWebSocket } from '@/hooks/useWebSocket'
import { AGENTS_CONFIG } from '@/config/agents.config'
import AgentCard from '@/components/shared/AgentCard'
import RoundTab from '@/components/shared/RoundTab'
import ModelBadge from '@/components/shared/ModelBadge'
import MarkdownRenderer from '@/components/shared/MarkdownRenderer'
import { toast } from '@/components/shared/Toast'

const ROUND_CONFIG = [
  {
    number: 1,
    label: "Round 1",
    sublabel: "Individual Analysis",
    icon: BarChart3,
    description: "All 6 agents analyze in parallel"
  },
  {
    number: 2,
    label: "Round 2",
    sublabel: "Council Debate",
    icon: MessageSquare,
    description: "Agents challenge each other's findings"
  },
  {
    number: 3,
    label: "Round 3",
    sublabel: "Final Verdict",
    icon: Crown,
    description: "Moderator synthesizes the decision"
  }
]

export default function Debate() {
  const store = useCouncilStore()
  const { 
    queryInput, setQueryInput, 
    activeRound, setActiveRound,
    completedRounds, setCompletedRounds,
    roundsUnlocked, setRoundsUnlocked,
    setJustUnlocked,
    agentOutputs, agentConfidence,
    selectedAgents, setSelectedAgents,
    reset, councilRunning, isStreaming
  } = store

  const { startStream, stopStream } = useCouncilStream()
  const socket = useWebSocket('council')

  useEffect(() => {
    const unsub = socket.on('round_complete', (data: any) => {
      const round = data.payload?.round || data.round
      if (round) {
        setCompletedRounds(prev => Array.from(new Set([...prev, round])))
        setRoundsUnlocked(prev => Array.from(new Set([...prev, round + 1])))
        setJustUnlocked(round + 1)
        setTimeout(() => setJustUnlocked(null), 2000)
        
        // Auto-navigate to next round
        if (round < 3) {
          setActiveRound(round + 1)
          toast('info', `🔓 Round ${round + 1} Unlocked — Agents are ready to debate`)
        }
      }
    })
    return unsub
  }, [socket, setCompletedRounds, setRoundsUnlocked, setJustUnlocked, setActiveRound])

  const handleQuerySubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryInput.trim() || isStreaming) return
    startStream(queryInput.trim())
  }

  const handleReset = () => {
    // Trigger fade-out (handled by AnimatePresence on the outer container)
    // and then reset the store
    reset()
    window.scrollTo({ top: 0, behavior: 'smooth' })
    toast('info', "Council Reset: Ready for a new supply chain analysis session.")
  }

  const toggleAgent = (id: string) => {
    if (selectedAgents.includes(id)) {
      setSelectedAgents(selectedAgents.filter(a => a !== id))
    } else {
      setSelectedAgents([...selectedAgents, id])
    }
  }

  const isRound3Complete = completedRounds.includes(3)

  return (
    <div className="flex h-screen bg-council-bg text-white overflow-hidden font-inter">
      {/* LEFT: MAIN DEBATE AREA */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        
        {/* TOP BAR / ROUNDS */}
        <div className="px-8 py-6 border-b border-white/[0.06] bg-council-bg/50 backdrop-blur-md z-20">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Crown className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-black tracking-tight font-outfit text-white">Supply Chain Command Center</h1>
                <p className="text-[11px] text-white/40 font-medium uppercase tracking-widest">Real-time market data, risk monitoring & council insights</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
               {ROUND_CONFIG.map((round) => (
                 <RoundTab
                   key={round.number}
                   {...round}
                   isCompleted={completedRounds.includes(round.number)}
                   isActive={activeRound === round.number}
                   isLocked={round.number > 1 && !completedRounds.includes(round.number - 1)}
                   onClick={() => setActiveRound(round.number)}
                 />
               ))}
            </div>
          </div>
        </div>

        {/* CHAT CONTENT */}
        <div className="flex-1 overflow-y-auto px-8 py-8 scrollbar-thin scrollbar-thumb-white/10">
          <AnimatePresence mode="wait">
            {!councilRunning && completedRounds.length === 0 ? (
              <motion.div 
                key="initial-state"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-2xl mx-auto mt-20 text-center"
              >
                <div className="inline-flex p-4 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 mb-6">
                  <Zap className="w-8 h-8 text-indigo-400" />
                </div>
                <h2 className="text-3xl font-bold font-poppins mb-4 text-gradient-indigo">Activate the Council</h2>
                <p className="text-white/50 leading-relaxed mb-10">
                  Ask a complex supply chain question. Seven specialized experts will analyze, debate, and synthesize a data-driven path forward.
                </p>
                
                <form onSubmit={handleQuerySubmit} className="relative group">
                  <input
                    type="text"
                    value={queryInput}
                    onChange={(e) => setQueryInput(e.target.value)}
                    placeholder="e.target.value = 'Analyze the impact of Red Sea disruptions on electronics OEMs...'"
                    className="w-full bg-white/[0.03] border border-white/10 rounded-2xl px-6 py-5 pr-16 text-lg focus:outline-none focus:border-indigo-500/50 focus:bg-white/[0.05] transition-all"
                  />
                  <button 
                    type="submit"
                    className="absolute right-3 top-3 bottom-3 px-4 bg-indigo-600 rounded-xl hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-900/40"
                  >
                    <ArrowRight className="w-5 h-5" />
                  </button>
                </form>
              </motion.div>
            ) : (
              <motion.div
                key="active-debate"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6 max-w-4xl mx-auto"
              >
                {/* AGENT OUTPUTS FOR CURRENT ROUND */}
                <div className="grid grid-cols-1 gap-6">
                  {Object.entries(agentOutputs).map(([agentId, content]) => {
                    const config = AGENTS_CONFIG.find(a => a.id === agentId)
                    if (!config) return null
                    
                    return (
                      <motion.div
                        layout
                        key={agentId}
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        className="glass-premium p-8 rounded-[2rem] relative overflow-hidden group"
                        style={{ 
                          borderColor: `${config.accentColor}30`,
                        }}
                      >
                         {/* TOP ACCENT BLOOM */}
                         <div className="absolute -top-24 -right-24 w-48 h-48 rounded-full blur-[80px] opacity-10 transition-opacity group-hover:opacity-20"
                              style={{ backgroundColor: config.accentColor }} />
                         
                         <div className="relative z-10">
                           <div className="flex items-start justify-between mb-8">
                             <div className="flex items-center gap-4">
                               <div className="w-14 h-14 rounded-2xl flex items-center justify-center border border-white/10 shadow-lg shadow-black/20"
                                    style={{ 
                                      background: `linear-gradient(135deg, ${config.accentColor}30 0%, ${config.accentColor}10 100%)`,
                                      borderColor: `${config.accentColor}40`
                                    }}>
                                 <span className="text-2xl drop-shadow-md">{config.emoji}</span>
                               </div>
                               <div>
                                 <h3 className="font-extrabold font-outfit text-2xl tracking-tight text-white mb-0.5">
                                   {config.name}
                                 </h3>
                                 <div className="flex items-center gap-2">
                                   <span className="text-[10px] text-white/30 uppercase tracking-[0.2em] font-bold">
                                     Round {activeRound} • Status: Complete
                                   </span>
                                   <div className="w-1 h-1 rounded-full bg-white/20" />
                                   <span className="text-[10px] font-bold" style={{ color: config.accentColor }}>
                                      {config.role.split('+')[0].trim()}
                                   </span>
                                 </div>
                               </div>
                             </div>

                             <div className="flex flex-col items-end gap-2">
                                {agentConfidence[agentId] && (
                                  <div className="px-3 py-1 rounded-full bg-white/5 border border-white/10 flex items-center gap-2 backdrop-blur-md">
                                    <div className="w-1.5 h-1.5 rounded-full animate-pulse shadow-[0_0_8px_rgba(255,255,255,0.5)]" style={{ backgroundColor: config.accentColor }} />
                                    <span className="text-xs font-black font-outfit" style={{ color: config.accentColor }}>
                                      {agentConfidence[agentId]}%
                                    </span>
                                  </div>
                                )}
                                <ModelBadge 
                                  model={config.model} 
                                  modelProvider={config.modelProvider} 
                                  modelColor={config.modelColor} 
                                  modelIcon={config.modelIcon} 
                                />
                             </div>
                           </div>

                           <div className="prose prose-invert max-w-none 
                                          text-white/80 leading-relaxed text-[15px] font-medium font-inter
                                          prose-headings:font-outfit prose-headings:text-white prose-headings:font-bold
                                          prose-strong:text-white prose-strong:font-bold prose-strong:font-outfit
                                          prose-p:mb-6 prose-li:mb-2
                                          selection:bg-white/10">
                             <MarkdownRenderer content={content} />
                           </div>
                           
                           {/* DECORATIVE BOTTOM LINE */}
                           <div className="mt-8 h-[1px] w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                         </div>
                      </motion.div>
                    )
                  })}
                </div>

                {/* FINAL RECOMMENDATION / RESET BUTTON */}
                {isRound3Complete && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.6, delay: 0.8, type: "spring" }}
                    className="flex justify-center py-10"
                  >
                    <button 
                      onClick={handleReset}
                      className="
                        group relative flex items-center gap-3 px-8 py-4
                        rounded-2xl font-semibold text-base tracking-wide
                        bg-gradient-to-r from-indigo-600/20 to-purple-600/20
                        hover:from-indigo-600/40 hover:to-purple-600/40
                        border border-indigo-500/30 hover:border-indigo-400/60
                        backdrop-filter backdrop-blur-xl
                        text-indigo-300 hover:text-white
                        shadow-lg shadow-indigo-900/30
                        hover:shadow-indigo-500/20 hover:shadow-xl
                        transition-all duration-300 ease-in-out
                        hover:scale-105 active:scale-95
                      "
                    >
                      <RotateCcw className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
                      Start New Council Session
                      <span className="absolute -top-2 -right-2 flex h-4 w-4">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-4 w-4 bg-indigo-500"></span>
                      </span>
                    </button>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* STOP BUTTON OVERLAY */}
        {isStreaming && (
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-30">
             <button 
               onClick={stopStream}
               className="flex items-center gap-2 px-6 py-3 bg-red-500/10 border border-red-500/30 rounded-full text-red-400 hover:bg-red-500/20 transition-all backdrop-blur-md"
             >
               <StopCircle className="w-4 h-4" />
               Halt Council Operation
             </button>
          </div>
        )}
      </div>

      {/* RIGHT: AGENTS SELECTION PANEL */}
      <div className="w-[320px] bg-council-surface border-l border-white/[0.06] flex flex-col z-20">
        
        {/* PANEL HEADER */}
        <div className="px-4 pt-5 pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
              <Users className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <h2 className="text-[17px] font-bold tracking-tight font-poppins text-gradient-indigo">
              Council Agents
            </h2>
          </div>
          <p className="text-[11px] text-white/35 font-medium tracking-wide pl-9 font-inter">
            7 Specialized AI Experts • Select to focus
          </p>

          <div className="flex items-center gap-2 mt-2.5 pl-9">
            <div className="flex -space-x-1">
              {selectedAgents.slice(0,3).map(id => (
                <div key={id} className="w-4 h-4 rounded-full border border-indigo-500/50 bg-indigo-500/20 flex items-center justify-center text-[7px]">
                  {AGENTS_CONFIG.find(a => a.id === id)?.emoji}
                </div>
              ))}
            </div>
            {selectedAgents.length > 0 && (
              <span className="text-[10px] text-indigo-400 font-semibold">
                {selectedAgents.length} active
              </span>
            )}
          </div>

          <div className="mt-3 flex gap-1">
            {[1, 2, 3].map(round => (
              <div
                key={round}
                className="flex-1 h-0.5 rounded-full transition-all duration-500"
                style={{
                  background: completedRounds.includes(round)
                    ? "linear-gradient(90deg, #6366f1, #a855f7)"
                    : activeRound === round
                    ? "rgba(99, 102, 241, 0.4)"
                    : "rgba(255,255,255,0.08)"
                }}
              />
            ))}
          </div>
          <div className="flex justify-between mt-1 px-0.5">
            {["Analysis", "Debate", "Verdict"].map((label, i) => (
              <span key={label} className="text-[8px] tracking-wider uppercase"
                style={{
                  color: completedRounds.includes(i+1) ? "#818cf8" : "rgba(255,255,255,0.25)"
                }}
              >
                {label}
              </span>
            ))}
          </div>
        </div>

        {/* AGENT LIST */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2.5 scrollbar-thin scrollbar-thumb-white/10 hover:scrollbar-thumb-indigo-500/30">
          <AnimatePresence mode="popLayout">
            {AGENTS_CONFIG.map(agent => (
              <AgentCard
                key={agent.id}
                agent={agent}
                isSelected={selectedAgents.includes(agent.id)}
                agentConfidence={agentConfidence}
                handleSelectAgent={toggleAgent}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* PANEL FOOTER */}
        <div className="px-4 py-3 border-t border-white/[0.06]">
          <div className="flex items-center justify-center gap-1.5 text-[9px] uppercase tracking-widest text-white/20 font-semibold">
            <Zap className="w-2.5 h-2.5 text-indigo-500/50" />
            Powered by LangGraph + AWS Bedrock
            <Zap className="w-2.5 h-2.5 text-indigo-500/50" />
          </div>
        </div>
      </div>
    </div>
  )
}
