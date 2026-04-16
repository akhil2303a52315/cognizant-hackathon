import { create } from 'zustand'
import type { AgentRoundState, ModeratorResult, SupervisorResult, CouncilV2StreamEvent } from '@/types/council'

const AGENT_KEYS = ['risk', 'supply', 'logistics', 'market', 'finance', 'brand'] as const
type AgentKey = typeof AGENT_KEYS[number]

interface AgentState {
  round1: AgentRoundState
  round2: AgentRoundState
}

export type PipelineStageKey = 'rag_fetching' | 'api_called' | 'mcp_fetched' | 'sources_ready'
export interface PipelineStageState {
  status: 'idle' | 'active' | 'done'
  detail: string
  count: number
}

interface CouncilV2State {
  sessionId: string | null
  query: string
  currentRound: number
  currentPhase: 'idle' | 'analysis' | 'debate' | 'supervisor'
  isStreaming: boolean
  agents: Record<string, AgentState>
  moderatorR1: ModeratorResult | null
  moderatorR2: ModeratorResult | null
  supervisorResult: SupervisorResult | null
  selectedAgent: string | null
  viewMode: 'agent' | 'moderator' | 'supervisor'
  streamError: string | null
  citationMaps: Record<string, Record<string, string>>
  pipelineStages: Record<PipelineStageKey, PipelineStageState>
  handleV2Event: (event: CouncilV2StreamEvent) => void
  setSelectedAgent: (agent: string | null) => void
  setViewMode: (mode: 'agent' | 'moderator' | 'supervisor') => void
  reset: () => void
  setStreaming: (streaming: boolean) => void
  setStreamError: (error: string | null) => void
}

function makeInitialAgents(): Record<string, AgentState> {
  const agents: Record<string, AgentState> = {}
  for (const key of AGENT_KEYS) {
    agents[key] = {
      round1: { status: 'idle', output: '', confidence: 0 },
      round2: { status: 'idle', output: '', confidence: 0 },
    }
  }
  return agents
}

const STAGE_KEYS: PipelineStageKey[] = ['rag_fetching', 'api_called', 'mcp_fetched', 'sources_ready']
function makeInitialStages(): Record<PipelineStageKey, PipelineStageState> {
  return Object.fromEntries(
    STAGE_KEYS.map((k) => [k, { status: 'idle', detail: '', count: 0 }])
  ) as Record<PipelineStageKey, PipelineStageState>
}

function isValidAgent(key: string): key is AgentKey {
  return (AGENT_KEYS as readonly string[]).includes(key)
}

function updateAgentRound(
  agents: Record<string, AgentState>,
  agentKey: string,
  roundKey: 'round1' | 'round2',
  update: Partial<AgentRoundState>
): Record<string, AgentState> {
  const current = agents[agentKey]
  if (!current) return agents
  const currentRound = current[roundKey]
  return {
    ...agents,
    [agentKey]: {
      ...current,
      [roundKey]: { ...currentRound, ...update },
    },
  }
}

export const useCouncilV2Store = create<CouncilV2State>((set) => ({
  sessionId: null,
  query: '',
  currentRound: 0,
  currentPhase: 'idle',
  isStreaming: false,
  agents: makeInitialAgents(),
  moderatorR1: null,
  moderatorR2: null,
  supervisorResult: null,
  selectedAgent: null,
  viewMode: 'agent',
  streamError: null,
  citationMaps: {},
  pipelineStages: makeInitialStages(),

  handleV2Event: (event) => {
    switch (event.type) {
      case 'start':
        set({
          isStreaming: true,
          streamError: null,
          sessionId: event.session_id || null,
          query: event.query || '',
          currentRound: 0,
          currentPhase: 'idle',
          agents: makeInitialAgents(),
          moderatorR1: null,
          moderatorR2: null,
          supervisorResult: null,
          selectedAgent: 'risk',
          viewMode: 'agent',
          citationMaps: {},
          pipelineStages: makeInitialStages(),
        })
        break

      case 'pipeline_stage': {
        const stageKey = (event as any).stage as PipelineStageKey | undefined
        if (stageKey && STAGE_KEYS.includes(stageKey)) {
          set((state) => {
            // Mark previous stages as done, current as active
            const newStages = { ...state.pipelineStages }
            const idx = STAGE_KEYS.indexOf(stageKey)
            STAGE_KEYS.forEach((k, i) => {
              if (i < idx) newStages[k] = { ...newStages[k], status: 'done' }
              else if (i === idx) newStages[k] = {
                status: 'active',
                detail: (event as any).detail || '',
                count: (event as any).count || 0,
              }
            })
            return { pipelineStages: newStages }
          })
        }
        break
      }

      case 'citations_ready':
        // Mark all stages done
        set(() => ({
          pipelineStages: Object.fromEntries(
            STAGE_KEYS.map((k) => [k, { status: 'done', detail: '', count: 0 }])
          ) as Record<PipelineStageKey, PipelineStageState>,
        }))
        break

      case 'round_start':
        set({
          currentRound: event.round || 1,
          currentPhase: (event.phase as 'analysis' | 'debate' | 'supervisor') || 'analysis',
        })
        break

      case 'agent_start': {
        const agentKey = event.agent || ''
        const roundKey: 'round1' | 'round2' = (event.round || 1) === 1 ? 'round1' : 'round2'
        if (isValidAgent(agentKey)) {
          set((state) => {
            const updates: Partial<CouncilV2State> = {
              agents: updateAgentRound(state.agents, agentKey, roundKey, { status: 'thinking', output: '', confidence: 0 }),
            }
            // Only auto-select if no agent is selected yet (first agent to start)
            if (!state.selectedAgent) {
              updates.selectedAgent = agentKey
              updates.viewMode = 'agent'
            }
            return updates
          })
        } else if (agentKey === 'supervisor') {
          set({ viewMode: 'supervisor', selectedAgent: 'supervisor' })
        }
        break
      }

      case 'token': {
        const agentKey = event.agent || ''
        const roundKey: 'round1' | 'round2' = (event.round || 1) === 1 ? 'round1' : 'round2'
        const content = event.content || ''

        if (agentKey === 'supervisor') {
          set((state) => ({
            supervisorResult: state.supervisorResult
              ? { ...state.supervisorResult, output: state.supervisorResult.output + content }
              : { output: content, confidence: 0 },
          }))
        } else if (isValidAgent(agentKey)) {
          set((state) => ({
            agents: updateAgentRound(state.agents, agentKey, roundKey, {
              output: (state.agents[agentKey]?.[roundKey]?.output || '') + content,
            }),
          }))
        }
        break
      }

      case 'agent_done': {
        const agentKey = event.agent || ''
        const roundKey: 'round1' | 'round2' = (event.round || 1) === 1 ? 'round1' : 'round2'
        const confidence = event.confidence || 0

        if (isValidAgent(agentKey)) {
          set((state) => ({
            agents: updateAgentRound(state.agents, agentKey, roundKey, { status: 'done', confidence }),
          }))
        }
        break
      }

      case 'agent_error': {
        const agentKey = event.agent || ''
        const roundKey: 'round1' | 'round2' = (event.round || 1) === 1 ? 'round1' : 'round2'
        const error = event.error || 'Unknown error'

        if (isValidAgent(agentKey)) {
          set((state) => ({
            agents: updateAgentRound(state.agents, agentKey, roundKey, {
              status: 'error',
              output: `Error: ${error}`,
              confidence: 0,
            }),
          }))
        }
        break
      }

      case 'moderator_start':
        set({ viewMode: 'moderator' })
        break

      case 'moderator_done': {
        const round = event.round || 1
        const modResult: ModeratorResult = {
          scores: event.scores || {},
          consensus: event.consensus || 0,
          summary: event.summary || '',
        }
        if (round === 1) {
          set({ moderatorR1: modResult })
        } else {
          set({ moderatorR2: modResult })
        }
        break
      }

      case 'supervisor_done': {
        set((state) => ({
          supervisorResult: {
            output: state.supervisorResult?.output || '',
            confidence: event.confidence || 0,
          },
          viewMode: 'supervisor',
        }))
        break
      }

      case 'complete':
        set({
          isStreaming: false,
          currentRound: 3,
          currentPhase: 'supervisor',
          viewMode: 'supervisor',
        })
        break
    }
  },

  setSelectedAgent: (agent) => set({ selectedAgent: agent, viewMode: 'agent' }),
  setViewMode: (mode) => set({ viewMode: mode }),
  reset: () =>
    set({
      sessionId: null,
      query: '',
      currentRound: 0,
      currentPhase: 'idle',
      isStreaming: false,
      agents: makeInitialAgents(),
      moderatorR1: null,
      moderatorR2: null,
      supervisorResult: null,
      selectedAgent: null,
      viewMode: 'agent',
      streamError: null,
      citationMaps: {},
      pipelineStages: makeInitialStages(),
    }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setStreamError: (error) => set({ streamError: error }),
}))
