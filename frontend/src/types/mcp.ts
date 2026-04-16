export interface MCPToolHealth {
  calls: number
  success_rate: number
  avg_latency_ms: number
  last_error: string | null
  last_success: string | null
}

export interface MCPTool {
  name: string
  description: string
  input_schema: {
    type: string
    properties: Record<string, MCPProperty>
    required?: string[]
  }
  category: string
  cache_ttl?: number
  allowed_agents?: string[]
  health?: MCPToolHealth
}

export interface MCPProperty {
  type: string
  description?: string
  default?: unknown
  items?: { type: string }
}

export interface MCPInvokeRequest {
  tool: string
  params: Record<string, unknown>
}

export interface MCPInvokeResponse {
  result: unknown
  tool: string
  latency_ms?: number
}
