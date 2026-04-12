export interface APIError {
  detail: string
  status_code: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface HealthStatus {
  status: 'ok' | 'degraded' | 'error'
  version: string
  uptime_seconds: number
  checks: Record<string, 'ok' | 'error' | 'unknown'>
}

export interface ModelInfo {
  id: string
  provider: string
  name: string
  available: boolean
  latency_ms?: number
}
