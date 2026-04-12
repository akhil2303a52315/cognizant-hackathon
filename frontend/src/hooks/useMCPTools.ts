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

export function useMCPInvoke() {
  return useMutation({
    mutationFn: async ({ tool, params }: { tool: string; params: Record<string, unknown> }) => {
      const { data } = await mcpApiMethods.invoke(tool, params)
      return data as MCPInvokeResponse
    },
  })
}
