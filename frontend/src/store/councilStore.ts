import { create } from 'zustand'
import type { CouncilSession, CouncilStreamEvent } from '@/types/council'

interface CouncilState {
  currentSession: CouncilSession | null
  messages: any[]
  currentRound: number
  activeRound: number
  completedRounds: number[]
  roundsUnlocked: number[]
  justUnlocked: number | null
  agentOutputs: Record<string, string>
  agentConfidence: Record<string, number>
  debateHistory: any[]
  finalRecommendation: any | null
  councilRunning: boolean
  selectedAgents: string[]
  queryInput: string
  isStreaming: boolean
  streamError: string | null

  setSession: (session: CouncilSession | null) => void
  setCurrentRound: (round: number) => void
  setActiveRound: (round: number) => void
  setCompletedRounds: (rounds: number[] | ((prev: number[]) => number[])) => void
  setRoundsUnlocked: (rounds: number[] | ((prev: number[]) => number[])) => void
  setJustUnlocked: (round: number | null) => void
  setAgentOutput: (agent: string, output: string) => void
  setAgentConfidence: (agent: string, confidence: number) => void
  setSelectedAgents: (agents: string[]) => void
  setQueryInput: (query: string) => void
  setStreaming: (streaming: boolean) => void
  setStreamError: (error: string | null) => void
  handleStreamEvent: (event: CouncilStreamEvent) => void
  reset: () => void
}

export const useCouncilStore = create<CouncilState>((set, get) => ({
  currentSession: null,
  messages: [],
  currentRound: 1,
  activeRound: 1,
  completedRounds: [],
  roundsUnlocked: [1],
  justUnlocked: null,
  agentOutputs: {},
  agentConfidence: {},
  debateHistory: [],
  finalRecommendation: null,
  councilRunning: false,
  selectedAgents: [],
  queryInput: "",
  isStreaming: false,
  streamError: null,

  setSession: (session) => set({ currentSession: session }),
  setCurrentRound: (round) => set({ currentRound: round }),
  setActiveRound: (round) => set({ activeRound: round }),
  setCompletedRounds: (updater) => set((state) => ({ 
    completedRounds: typeof updater === 'function' ? updater(state.completedRounds) : updater 
  })),
  setRoundsUnlocked: (updater) => set((state) => ({ 
    roundsUnlocked: typeof updater === 'function' ? updater(state.roundsUnlocked) : updater 
  })),
  setJustUnlocked: (round) => set({ justUnlocked: round }),
  setAgentOutput: (agent, output) =>
    set((state) => ({
      agentOutputs: { ...state.agentOutputs, [agent]: output },
    })),
  setAgentConfidence: (agent, confidence) =>
    set((state) => ({
      agentConfidence: { ...state.agentConfidence, [agent]: confidence },
    })),
  setSelectedAgents: (agents) => set({ selectedAgents: agents }),
  setQueryInput: (query) => set({ queryInput: query }),
  setStreaming: (streaming) => set({ isStreaming: streaming, councilRunning: streaming }),
  setStreamError: (error) => set({ streamError: error }),

  handleStreamEvent: (event) => {
    switch (event.type) {
      case 'start':
        set({
          isStreaming: true,
          councilRunning: true,
          streamError: null,
          agentOutputs: {},
          agentConfidence: {},
          completedRounds: [],
          roundsUnlocked: [1],
          currentRound: 1,
          activeRound: 1,
          currentSession: {
            session_id: event.session_id || '',
            query: get().queryInput,
            recommendation: null,
            confidence: null,
            agent_outputs: [],
            evidence: [],
            debate_history: [],
            round_number: 1,
            status: 'streaming',
            latency_ms: 0,
          },
        })
        break
      case 'agent_start':
        set((state) => ({
          agentOutputs: { ...state.agentOutputs, [event.agent || '']: '' },
        }))
        break
      case 'token':
        if (event.agent && event.content) {
          set((state) => ({
            agentOutputs: {
              ...state.agentOutputs,
              [event.agent!]: (state.agentOutputs[event.agent!] || '') + event.content,
            },
          }))
        }
        break
      case 'agent_done':
        break
      case 'agent_error':
        if (event.agent && event.error) {
          set((state) => ({
            agentOutputs: { ...state.agentOutputs, [event.agent!]: `Error: ${event.error}` },
          }))
        }
        break
      case 'complete':
        set((state) => ({
          isStreaming: false,
          councilRunning: false,
          completedRounds: [...state.completedRounds, state.currentRound],
          currentSession: state.currentSession
            ? {
                ...state.currentSession,
                status: 'complete',
                recommendation: event.recommendation || null,
              }
            : null,
          finalRecommendation: event.recommendation ? { text: event.recommendation } : null
        }))
        break
    }
  },

  reset: () =>
    set({
      messages: [],
      currentRound: 1,
      activeRound: 1,
      completedRounds: [],
      roundsUnlocked: [1],
      agentOutputs: {},
      agentConfidence: {},
      debateHistory: [],
      finalRecommendation: null,
      councilRunning: false,
      selectedAgents: [],
      queryInput: "",
      isStreaming: false,
      streamError: null,
      currentSession: null,
    }),
}))
