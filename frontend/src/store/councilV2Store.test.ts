import { describe, it, expect, beforeEach } from 'vitest'
import { useCouncilV2Store } from './councilV2Store'
import type { CouncilV2StreamEvent } from '@/types/council'

describe('councilV2Store', () => {
  beforeEach(() => {
    useCouncilV2Store.getState().reset()
  })

  it('starts with idle state', () => {
    const state = useCouncilV2Store.getState()
    expect(state.isStreaming).toBe(false)
    expect(state.currentRound).toBe(0)
    expect(state.currentPhase).toBe('idle')
    expect(state.selectedAgent).toBeNull()
    expect(state.viewMode).toBe('agent')
    expect(state.streamError).toBeNull()
    expect(state.moderatorR1).toBeNull()
    expect(state.moderatorR2).toBeNull()
    expect(state.supervisorResult).toBeNull()
  })

  it('initializes all 7 agents with idle status', () => {
    const { agents } = useCouncilV2Store.getState()
    const keys = Object.keys(agents)
    expect(keys).toHaveLength(7)
    expect(keys).toContain('analyst')
    expect(keys).toContain('critic')
    expect(keys).toContain('creative')
    expect(keys).toContain('risk')
    expect(keys).toContain('legal')
    expect(keys).toContain('market')
    expect(keys).toContain('optimizer')

    for (const key of keys) {
      const agent = agents[key]!
      expect(agent.round1.status).toBe('idle')
      expect(agent.round2.status).toBe('idle')
      expect(agent.round1.output).toBe('')
      expect(agent.round2.output).toBe('')
      expect(agent.round1.confidence).toBe(0)
      expect(agent.round2.confidence).toBe(0)
    }
  })

  it('handles start event', () => {
    const event: CouncilV2StreamEvent = {
      type: 'start',
      session_id: 'test-session-1',
      query: 'What are supply chain risks?',
    }
    useCouncilV2Store.getState().handleV2Event(event)

    const state = useCouncilV2Store.getState()
    expect(state.isStreaming).toBe(true)
    expect(state.sessionId).toBe('test-session-1')
    expect(state.query).toBe('What are supply chain risks?')
    expect(state.selectedAgent).toBe('analyst')
    expect(state.viewMode).toBe('agent')
  })

  it('handles round_start event', () => {
    const event: CouncilV2StreamEvent = {
      type: 'round_start',
      round: 1,
      phase: 'analysis',
    }
    useCouncilV2Store.getState().handleV2Event(event)

    const state = useCouncilV2Store.getState()
    expect(state.currentRound).toBe(1)
    expect(state.currentPhase).toBe('analysis')
  })

  it('handles agent_start for round 1', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'start', session_id: 's1' })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_start', agent: 'analyst', round: 1 })

    const state = useCouncilV2Store.getState()
    expect(state.agents.analyst!.round1.status).toBe('thinking')
    expect(state.agents.analyst!.round1.output).toBe('')
    expect(state.selectedAgent).toBe('analyst')
  })

  it('handles token event for agent', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'start', session_id: 's1' })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_start', agent: 'critic', round: 1 })
    useCouncilV2Store.getState().handleV2Event({ type: 'token', agent: 'critic', round: 1, content: 'Hello ' })
    useCouncilV2Store.getState().handleV2Event({ type: 'token', agent: 'critic', round: 1, content: 'World' })

    const state = useCouncilV2Store.getState()
    expect(state.agents.critic!.round1.output).toBe('Hello World')
  })

  it('handles agent_done event', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'start', session_id: 's1' })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_start', agent: 'risk', round: 1 })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_done', agent: 'risk', round: 1, confidence: 87 })

    const state = useCouncilV2Store.getState()
    expect(state.agents.risk!.round1.status).toBe('done')
    expect(state.agents.risk!.round1.confidence).toBe(87)
  })

  it('handles agent_error event', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'start', session_id: 's1' })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_start', agent: 'legal', round: 1 })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_error', agent: 'legal', round: 1, error: 'Timeout' })

    const state = useCouncilV2Store.getState()
    expect(state.agents.legal!.round1.status).toBe('error')
    expect(state.agents.legal!.round1.output).toBe('Error: Timeout')
  })

  it('handles token for supervisor', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'start', session_id: 's1' })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_start', agent: 'supervisor', round: 3 })
    useCouncilV2Store.getState().handleV2Event({ type: 'token', agent: 'supervisor', round: 3, content: 'Final ' })
    useCouncilV2Store.getState().handleV2Event({ type: 'token', agent: 'supervisor', round: 3, content: 'Verdict' })

    const state = useCouncilV2Store.getState()
    expect(state.supervisorResult).not.toBeNull()
    expect(state.supervisorResult!.output).toBe('Final Verdict')
  })

  it('handles moderator_start event', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'moderator_start', round: 1 })
    expect(useCouncilV2Store.getState().viewMode).toBe('moderator')
  })

  it('handles moderator_done for round 1', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'moderator_done',
      round: 1,
      scores: { analyst: 85, critic: 70, creative: 60, risk: 80, legal: 75, market: 65, optimizer: 90 },
      consensus: 75,
      summary: 'Good analysis overall',
    })

    const state = useCouncilV2Store.getState()
    expect(state.moderatorR1).not.toBeNull()
    expect(state.moderatorR1!.consensus).toBe(75)
    expect(state.moderatorR1!.scores.analyst).toBe(85)
    expect(state.moderatorR1!.summary).toBe('Good analysis overall')
  })

  it('handles moderator_done for round 2', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'moderator_done',
      round: 2,
      scores: { analyst: 90, critic: 80, creative: 70, risk: 85, legal: 80, market: 75, optimizer: 95 },
      consensus: 85,
      summary: 'Strong consensus reached',
    })

    const state = useCouncilV2Store.getState()
    expect(state.moderatorR2).not.toBeNull()
    expect(state.moderatorR2!.consensus).toBe(85)
  })

  it('handles supervisor_done event', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'start', session_id: 's1' })
    // Build up supervisor output first
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_start', agent: 'supervisor', round: 3 })
    useCouncilV2Store.getState().handleV2Event({ type: 'token', agent: 'supervisor', round: 3, content: 'Verdict text' })
    useCouncilV2Store.getState().handleV2Event({ type: 'supervisor_done', round: 3, confidence: 92 })

    const state = useCouncilV2Store.getState()
    expect(state.supervisorResult).not.toBeNull()
    expect(state.supervisorResult!.output).toBe('Verdict text')
    expect(state.supervisorResult!.confidence).toBe(92)
    expect(state.viewMode).toBe('supervisor')
  })

  it('handles complete event', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'start', session_id: 's1' })
    useCouncilV2Store.getState().handleV2Event({ type: 'complete', session_id: 's1' })

    const state = useCouncilV2Store.getState()
    expect(state.isStreaming).toBe(false)
    expect(state.currentRound).toBe(3)
    expect(state.currentPhase).toBe('supervisor')
    expect(state.viewMode).toBe('supervisor')
  })

  it('handles full 3-round flow', () => {
    const store = useCouncilV2Store.getState()

    // Start
    store.handleV2Event({ type: 'start', session_id: 'full-flow', query: 'Test query' })

    // Round 1
    store.handleV2Event({ type: 'round_start', round: 1, phase: 'analysis' })
    store.handleV2Event({ type: 'agent_start', agent: 'analyst', round: 1 })
    store.handleV2Event({ type: 'token', agent: 'analyst', round: 1, content: 'Analysis output' })
    store.handleV2Event({ type: 'agent_done', agent: 'analyst', round: 1, confidence: 80 })
    store.handleV2Event({ type: 'moderator_done', round: 1, scores: { analyst: 80 }, consensus: 70, summary: 'R1 summary' })

    // Round 2
    store.handleV2Event({ type: 'round_start', round: 2, phase: 'debate' })
    store.handleV2Event({ type: 'agent_start', agent: 'analyst', round: 2 })
    store.handleV2Event({ type: 'token', agent: 'analyst', round: 2, content: 'Debate output' })
    store.handleV2Event({ type: 'agent_done', agent: 'analyst', round: 2, confidence: 90 })
    store.handleV2Event({ type: 'moderator_done', round: 2, scores: { analyst: 90 }, consensus: 85, summary: 'R2 summary' })

    // Round 3
    store.handleV2Event({ type: 'round_start', round: 3, phase: 'supervisor' })
    store.handleV2Event({ type: 'agent_start', agent: 'supervisor', round: 3 })
    store.handleV2Event({ type: 'token', agent: 'supervisor', round: 3, content: 'Final verdict' })
    store.handleV2Event({ type: 'supervisor_done', round: 3, confidence: 88 })
    store.handleV2Event({ type: 'complete', session_id: 'full-flow' })

    const state = useCouncilV2Store.getState()
    expect(state.isStreaming).toBe(false)
    expect(state.currentRound).toBe(3)
    expect(state.agents.analyst!.round1.output).toBe('Analysis output')
    expect(state.agents.analyst!.round1.confidence).toBe(80)
    expect(state.agents.analyst!.round2.output).toBe('Debate output')
    expect(state.agents.analyst!.round2.confidence).toBe(90)
    expect(state.moderatorR1!.consensus).toBe(70)
    expect(state.moderatorR2!.consensus).toBe(85)
    expect(state.supervisorResult!.output).toBe('Final verdict')
    expect(state.supervisorResult!.confidence).toBe(88)
  })

  it('setSelectedAgent switches view to agent mode', () => {
    useCouncilV2Store.getState().setViewMode('moderator')
    expect(useCouncilV2Store.getState().viewMode).toBe('moderator')

    useCouncilV2Store.getState().setSelectedAgent('risk')
    const state = useCouncilV2Store.getState()
    expect(state.selectedAgent).toBe('risk')
    expect(state.viewMode).toBe('agent')
  })

  it('setViewMode changes view', () => {
    useCouncilV2Store.getState().setViewMode('supervisor')
    expect(useCouncilV2Store.getState().viewMode).toBe('supervisor')

    useCouncilV2Store.getState().setViewMode('moderator')
    expect(useCouncilV2Store.getState().viewMode).toBe('moderator')
  })

  it('reset clears all state', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'start', session_id: 's1' })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_start', agent: 'analyst', round: 1 })
    useCouncilV2Store.getState().handleV2Event({ type: 'token', agent: 'analyst', round: 1, content: 'Some output' })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_done', agent: 'analyst', round: 1, confidence: 75 })

    useCouncilV2Store.getState().reset()

    const state = useCouncilV2Store.getState()
    expect(state.isStreaming).toBe(false)
    expect(state.sessionId).toBeNull()
    expect(state.query).toBe('')
    expect(state.currentRound).toBe(0)
    expect(state.agents.analyst!.round1.status).toBe('idle')
    expect(state.agents.analyst!.round1.output).toBe('')
    expect(state.moderatorR1).toBeNull()
    expect(state.supervisorResult).toBeNull()
  })

  it('ignores events for unknown agents', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'start', session_id: 's1' })
    useCouncilV2Store.getState().handleV2Event({ type: 'agent_start', agent: 'unknown_agent', round: 1 })
    useCouncilV2Store.getState().handleV2Event({ type: 'token', agent: 'unknown_agent', round: 1, content: 'test' })

    const state = useCouncilV2Store.getState()
    expect(Object.keys(state.agents)).toHaveLength(7)
    expect(state.agents).not.toHaveProperty('unknown_agent')
  })

  it('handles stream error', () => {
    useCouncilV2Store.getState().setStreamError('Connection failed')
    expect(useCouncilV2Store.getState().streamError).toBe('Connection failed')

    useCouncilV2Store.getState().setStreamError(null)
    expect(useCouncilV2Store.getState().streamError).toBeNull()
  })
})
