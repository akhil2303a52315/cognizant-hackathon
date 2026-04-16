import { useCallback, useRef } from 'react'
import { useCouncilV2Store } from '@/store/councilV2Store'
import type { CouncilWSEvent } from '@/types/council'

const WS_BASE = (import.meta.env.VITE_WS_URL as string) || ''
const RECONNECT_DELAY = 2000
const MAX_RECONNECT = 3

export function useCouncilGraphStream() {
  const { handleV2Event, isStreaming, reset, setStreaming, setStreamError } = useCouncilV2Store()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef(0)

  const startStream = useCallback((query: string) => {
    reset()
    setStreaming(true)
    reconnectCountRef.current = 0

    const wsUrl = WS_BASE
      ? `${WS_BASE}/observability/ws/debate`
      : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/observability/ws/debate`

    const connect = () => {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectCountRef.current = 0
        // Send start action with the query
        ws.send(JSON.stringify({ action: 'start', query }))
      }

      ws.onmessage = (event) => {
        try {
          const payload: CouncilWSEvent = JSON.parse(event.data)
          handleV2Event(wsEventToV2Event(payload))
        } catch {
          // skip malformed JSON
        }
      }

      ws.onerror = () => {
        setStreamError('WebSocket connection error')
      }

      ws.onclose = (event) => {
        // Attempt reconnect if not a normal close and still streaming
        if (!event.wasClean && reconnectCountRef.current < MAX_RECONNECT && useCouncilV2Store.getState().isStreaming) {
          reconnectCountRef.current++
          setTimeout(connect, RECONNECT_DELAY)
        } else if (useCouncilV2Store.getState().isStreaming) {
          setStreaming(false)
          setStreamError('WebSocket connection lost')
        }
      }
    }

    connect()
  }, [handleV2Event, reset, setStreaming, setStreamError])

  const stopStream = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'User stopped')
      wsRef.current = null
    }
    setStreaming(false)
  }, [setStreaming])

  const approveHumanReview = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'approve' }))
    }
  }, [])

  return { startStream, stopStream, isStreaming, approveHumanReview }
}

/**
 * Map full graph WebSocket events to the V2 stream event format
 * so the existing councilV2Store can handle them without changes.
 */
function wsEventToV2Event(ws: CouncilWSEvent): import('@/types/council').CouncilV2StreamEvent {
  switch (ws.type) {
    case 'agent_done':
      return {
        type: 'agent_done',
        agent: ws.data.agent,
        confidence: ws.data.confidence,
        session_id: ws.data.session_id,
      }
    case 'debate_round':
      return {
        type: 'moderator_done',
        round: ws.data.debate_rounds?.length,
        consensus: ws.data.confidence,
        session_id: ws.data.session_id,
      }
    case 'complete':
      return {
        type: 'complete',
        session_id: ws.data.session_id,
        recommendation: ws.data.recommendation,
        confidence: ws.data.confidence,
      }
    case 'human_review_needed':
      return {
        type: 'agent_error',
        agent: 'moderator',
        error: 'Human review required — click Approve to continue',
        session_id: ws.data.session_id,
      }
    case 'heartbeat':
      return { type: 'start' } // no-op, just keepalive
    default:
      return { type: 'start' }
  }
}
