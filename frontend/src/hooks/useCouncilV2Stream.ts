import { useCallback, useRef } from 'react'
import { getClientApiKey } from '@/lib/clientApiKey'
import { useCouncilV2Store } from '@/store/councilV2Store'
import type { CouncilV2StreamEvent } from '@/types/council'

export function useCouncilV2Stream() {
  const { handleV2Event, isStreaming, reset, setStreaming, setStreamError } = useCouncilV2Store()
  const abortRef = useRef<AbortController | null>(null)

  const startStream = useCallback(async (query: string) => {
    reset()
    abortRef.current = new AbortController()

    try {
      const apiKey = getClientApiKey()
      const response = await fetch('/api/council/v2/stream', {
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
              const event: CouncilV2StreamEvent = JSON.parse(line.slice(6))
              handleV2Event(event)
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setStreamError(err.message)
        setStreaming(false)
      }
    }
  }, [handleV2Event, reset, setStreamError, setStreaming])

  const stopStream = useCallback(() => {
    abortRef.current?.abort()
    setStreaming(false)
  }, [setStreaming])

  return { startStream, stopStream, isStreaming }
}
