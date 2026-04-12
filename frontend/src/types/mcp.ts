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
