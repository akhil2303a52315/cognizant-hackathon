import { useCallback, useRef } from 'react'
import { useCouncilStore } from '@/store/councilStore'
import type { CouncilStreamEvent } from '@/types/council'

export function useCouncilStream() {
  const { handleStreamEvent, isStreaming, agentOutputs, currentSession, reset } = useCouncilStore()
  const abortRef = useRef<AbortController | null>(null)

  const startStream = useCallback(async (query: string) => {
    reset()
    abortRef.current = new AbortController()

    try {
      const apiKey = localStorage.getItem('api_key') || 'dev-key'
      const response = await fetch('/council/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({ query }),
        signal: abortRef.current.signal,
      })

      if (!response.ok || !response.body) {
        throw new Error(`Stream failed: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: CouncilStreamEvent = JSON.parse(line.slice(6))
              handleStreamEvent(event)
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        useCouncilStore.getState().setStreamError(err.message)
      }
    }
  }, [handleStreamEvent, reset])

  const stopStream = useCallback(() => {
    abortRef.current?.abort()
    useCouncilStore.getState().setStreaming(false)
  }, [])

  return { startStream, stopStream, isStreaming, agentOutputs, currentSession }
}
