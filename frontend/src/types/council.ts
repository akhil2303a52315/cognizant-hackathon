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
  type: 'start' | 'round_start' | 'agent_start' | 'token' | 'agent_done' | 'agent_error' | 'moderator_start' | 'moderator_done' | 'supervisor_done' | 'complete' | 'pipeline_stage' | 'citations_ready' | 'citations_map' | 'source_discovered'
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
  stage?: string
  detail?: string
  count?: number
  urls?: Record<string, string>
  sources?: Array<{num: number, title: string, url: string}>
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

// ---------------------------------------------------------------------------
// Full graph pipeline types (from LangGraph council)
// ---------------------------------------------------------------------------

export interface Prediction {
  type: 'price' | 'disruption' | 'lead_time'
  label: string
  value: number
  unit: string
  confidence: number
  horizon: string
}

export interface TieredFallback {
  type: 'tier1_immediate' | 'tier2_shortterm' | 'tier3_strategic'
  details: string
  cost_estimate: number
  time_to_implement: string
}

export interface BrandSentiment {
  overall_sentiment: string
  sentiment_score: number
  crisis_detected: boolean
  crisis_comms?: string
  ad_pivot?: string
  competitor_analysis?: Record<string, unknown>
}

export interface CouncilGraphResult {
  session_id: string
  query: string
  recommendation: string
  confidence: number
  risk_score: number
  debate_rounds: DebateRound[]
  agent_outputs: AgentOutput[]
  predictions: Prediction[]
  tiered_fallbacks: TieredFallback[]
  brand_sentiment: BrandSentiment | null
  debate_history: { round: number; phase: string; confidence: number }[]
}

/** WebSocket event from /observability/ws/debate full graph pipeline */
export interface CouncilWSEvent {
  type: 'agent_done' | 'debate_round' | 'complete' | 'human_review_needed' | 'heartbeat'
  data: {
    session_id?: string
    agent?: string
    confidence?: number
    contribution?: string
    debate_rounds?: DebateRound[]
    recommendation?: string
    risk_score?: number
  }
}

export const COUNCIL_AGENTS: AgentInfo[] = [
  { key: 'risk', label: 'Risk Sentinel', color: 'bg-red-500', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-700', dotColor: 'bg-red-500', hexColor: '#EF4444' },
  { key: 'supply', label: 'Supply Optimizer', color: 'bg-violet-500', bgColor: 'bg-violet-50', borderColor: 'border-violet-200', textColor: 'text-violet-700', dotColor: 'bg-violet-500', hexColor: '#7C3AED' },
  { key: 'logistics', label: 'Logistics Navigator', color: 'bg-cyan-500', bgColor: 'bg-cyan-50', borderColor: 'border-cyan-200', textColor: 'text-cyan-700', dotColor: 'bg-cyan-500', hexColor: '#06B6D4' },
  { key: 'market', label: 'Market Intelligence', color: 'bg-amber-500', bgColor: 'bg-amber-50', borderColor: 'border-amber-200', textColor: 'text-amber-700', dotColor: 'bg-amber-500', hexColor: '#F97316' },
  { key: 'finance', label: 'Finance Guardian', color: 'bg-emerald-500', bgColor: 'bg-emerald-50', borderColor: 'border-emerald-200', textColor: 'text-emerald-700', dotColor: 'bg-emerald-500', hexColor: '#059669' },
  { key: 'brand', label: 'Brand Protector', color: 'bg-pink-500', bgColor: 'bg-pink-50', borderColor: 'border-pink-200', textColor: 'text-pink-700', dotColor: 'bg-pink-500', hexColor: '#EC4899' },
]

/** @deprecated Use COUNCIL_AGENTS instead */
export const SEVEN_AGENTS = COUNCIL_AGENTS
