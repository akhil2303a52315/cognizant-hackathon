export interface AgentOutput {
  agent: string
  output: string
  confidence: number
  evidence: string[]
}

export interface DebateRound {
  round_number: number
  agent_positions: Record<string, string>
  disagreements: string[]
  resolutions: string[]
}

export interface CouncilSession {
  session_id: string
  query: string
  recommendation: string | null
  confidence: number | null
  agent_outputs: AgentOutput[]
  evidence: string[]
  debate_history: DebateRound[]
  round_number: number
  status: 'pending' | 'streaming' | 'complete' | 'error'
  latency_ms: number
  context?: Record<string, unknown>
}

export interface CouncilRequest {
  query: string
  context?: Record<string, unknown>
  ws_session_id?: string
}

export interface CouncilStreamEvent {
  type: 'start' | 'agent_start' | 'token' | 'agent_done' | 'agent_error' | 'complete'
  agent?: string
  content?: string
  error?: string
  session_id?: string
  recommendation?: string
}

export interface Recommendation {
  text: string
  confidence: number
  supporting_agents: string[]
  risk_level: 'low' | 'medium' | 'high' | 'critical'
}
