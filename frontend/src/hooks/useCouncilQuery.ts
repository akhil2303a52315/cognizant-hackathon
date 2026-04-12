import { useMutation } from '@tanstack/react-query'
import { councilApi } from '@/lib/api'
import type { CouncilSession } from '@/types/council'

export function useCouncilQuery() {
  return useMutation({
    mutationFn: async (query: string) => {
      const { data } = await councilApi.analyze(query)
      return data as CouncilSession
    },
  })
}
