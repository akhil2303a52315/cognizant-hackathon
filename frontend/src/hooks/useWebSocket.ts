import { useEffect, useRef, useCallback } from 'react'
import wsClient from '@/lib/socket'

export function useWebSocket(topic?: string) {
  const connectedRef = useRef(false)

  useEffect(() => {
    if (!wsClient.connected) {
      wsClient.connect()
    }

    if (topic) {
      wsClient.subscribe(topic)
    }

    connectedRef.current = wsClient.connected

    return () => {
      if (topic) {
        wsClient.unsubscribe(topic)
      }
    }
  }, [topic])

  const on = useCallback((eventType: string, handler: (event: unknown) => void) => {
    wsClient.on(eventType, handler as Parameters<typeof wsClient.on>[1])
    return () => wsClient.off(eventType, handler as Parameters<typeof wsClient.off>[1])
  }, [])

  return { connected: connectedRef.current, on }
}
