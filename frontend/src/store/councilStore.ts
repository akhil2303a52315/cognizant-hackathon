import { create } from 'zustand'
import type { CouncilSession, CouncilStreamEvent } from '@/types/council'

interface CouncilState {
  currentSession: CouncilSession | null
  agentOutputs: Record<string, string>
  isStreaming: boolean
  streamError: string | null
  history: CouncilSession[]

  setSession: (session: CouncilSession | null) => void
  appendToken: (agent: string, token: string) => void
  setAgentOutput: (agent: string, output: string) => void
  setStreaming: (streaming: boolean) => void
  setStreamError: (error: string | null) => void
  handleStreamEvent: (event: CouncilStreamEvent) => void
  addToHistory: (session: CouncilSession) => void
  reset: () => void
}

export const useCouncilStore = create<CouncilState>((set, get) => ({
  currentSession: null,
  agentOutputs: {},
  isStreaming: false,
  streamError: null,
  history: [],

  setSession: (session) => set({ currentSession: session }),

  appendToken: (agent, token) =>
    set((state) => ({
      agentOutputs: {
        ...state.agentOutputs,
        [agent]: (state.agentOutputs[agent] || '') + token,
      },
    })),

  setAgentOutput: (agent, output) =>
    set((state) => ({
      agentOutputs: { ...state.agentOutputs, [agent]: output },
    })),

  setStreaming: (streaming) => set({ isStreaming: streaming }),

  setStreamError: (error) => set({ streamError: error }),

  handleStreamEvent: (event) => {
    switch (event.type) {
      case 'start':
        set({
          isStreaming: true,
          streamError: null,
          agentOutputs: {},
          currentSession: {
            session_id: event.session_id || '',
            query: '',
            recommendation: null,
            confidence: null,
            agent_outputs: [],
            evidence: [],
            debate_history: [],
            round_number: 0,
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
          get().appendToken(event.agent, event.content)
        }
        break
      case 'agent_done':
        break
      case 'agent_error':
        if (event.agent && event.error) {
          get().setAgentOutput(event.agent, `Error: ${event.error}`)
        }
        break
      case 'complete':
        set((state) => ({
          isStreaming: false,
          currentSession: state.currentSession
            ? {
                ...state.currentSession,
                status: 'complete',
                recommendation: event.recommendation || null,
              }
            : null,
        }))
        break
    }
  },

  addToHistory: (session) =>
    set((state) => ({ history: [session, ...state.history] })),

  reset: () =>
    set({
      currentSession: null,
      agentOutputs: {},
      isStreaming: false,
      streamError: null,
    }),
}))
