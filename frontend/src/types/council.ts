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

export type AgentStatus = 'idle' | 'thinking' | 'done' | 'error'

export interface AgentInfo {
  key: string
  label: string
  color: string
  bgColor: string
  borderColor: string
  textColor: string
  dotColor: string
  hexColor: string
}

export interface AgentRoundState {
  status: AgentStatus
  output: string
  confidence: number
}

export interface ModeratorResult {
  scores: Record<string, number>
  consensus: number
  summary: string
}

export interface SupervisorResult {
  output: string
  confidence: number
}

export interface CouncilV2StreamEvent {
  type: 'start' | 'round_start' | 'agent_start' | 'token' | 'agent_done' | 'agent_error' | 'moderator_start' | 'moderator_done' | 'supervisor_done' | 'complete'
  session_id?: string
  query?: string
  round?: number
  phase?: string
  agent?: string
  content?: string
  error?: string
  confidence?: number
  scores?: Record<string, number>
  consensus?: number
  summary?: string
  recommendation?: string
  output_preview?: string
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

export const SEVEN_AGENTS: AgentInfo[] = [
  { key: 'analyst', label: 'Analyst', color: 'bg-blue-500', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-700', dotColor: 'bg-blue-500', hexColor: '#3B82F6' },
  { key: 'critic', label: 'Critic', color: 'bg-red-500', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-700', dotColor: 'bg-red-500', hexColor: '#EF4444' },
  { key: 'creative', label: 'Creative', color: 'bg-purple-500', bgColor: 'bg-purple-50', borderColor: 'border-purple-200', textColor: 'text-purple-700', dotColor: 'bg-purple-500', hexColor: '#A855F7' },
  { key: 'risk', label: 'Risk', color: 'bg-amber-500', bgColor: 'bg-amber-50', borderColor: 'border-amber-200', textColor: 'text-amber-700', dotColor: 'bg-amber-500', hexColor: '#F97316' },
  { key: 'legal', label: 'Legal', color: 'bg-emerald-500', bgColor: 'bg-emerald-50', borderColor: 'border-emerald-200', textColor: 'text-emerald-700', dotColor: 'bg-emerald-500', hexColor: '#22C55E' },
  { key: 'market', label: 'Market', color: 'bg-pink-500', bgColor: 'bg-pink-50', borderColor: 'border-pink-200', textColor: 'text-pink-700', dotColor: 'bg-pink-500', hexColor: '#EC4899' },
  { key: 'optimizer', label: 'Optimizer', color: 'bg-cyan-500', bgColor: 'bg-cyan-50', borderColor: 'border-cyan-200', textColor: 'text-cyan-700', dotColor: 'bg-cyan-500', hexColor: '#06B6D4' },
]
