import { useQuery, useMutation } from '@tanstack/react-query'
import { mcpApiMethods } from '@/lib/api'
import type { MCPTool, MCPInvokeResponse } from '@/types/mcp'

export function useMCPTools() {
  return useQuery({
    queryKey: ['mcp-tools'],
    queryFn: async () => {
      const { data } = await mcpApiMethods.listTools()
      return data.tools as MCPTool[]
    },
    staleTime: 60000,
  })
}

export function useMCPManifest() {
  return useQuery({
    queryKey: ['mcp-manifest'],
    queryFn: async () => {
      const { data } = await mcpApiMethods.manifest()
      return data as { tools: MCPTool[]; categories: string[]; total_tools: number }
    },
    staleTime: 30000,
  })
}

export function useMCPToolsForAgent(agent: string) {
  return useQuery({
    queryKey: ['mcp-tools', agent],
    queryFn: async () => {
      const { data } = await mcpApiMethods.toolsForAgent(agent)
      return data as { agent: string; tools: MCPTool[]; total: number }
    },
    staleTime: 60000,
    enabled: !!agent,
  })
}

export function useMCPHealth() {
  return useQuery({
    queryKey: ['mcp-health'],
    queryFn: async () => {
      const { data } = await mcpApiMethods.health()
      return data as Record<string, { calls: number; success_rate: number; avg_latency_ms: number; last_error: string | null }>
    },
    staleTime: 15000,
  })
}

export function useMCPInvoke() {
  return useMutation({
    mutationFn: async ({ tool, params }: { tool: string; params: Record<string, unknown> }) => {
      const { data } = await mcpApiMethods.invoke(tool, params)
      return data as MCPInvokeResponse
    },
  })
}
