import axios from 'axios'
import type { APIError } from '@/types/api'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach API key
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('api_key') || 'dev-key'
  config.headers['X-API-Key'] = apiKey
  return config
})

// Response interceptor — handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        const err: APIError = { detail: 'Invalid API key', status_code: 401 }
        return Promise.reject(err)
      }
      if (status === 429) {
        const err: APIError = { detail: 'Rate limit exceeded', status_code: 429 }
        return Promise.reject(err)
      }
      if (status >= 500) {
        const err: APIError = { detail: error.response.data?.detail || 'Server error', status_code: status }
        return Promise.reject(err)
      }
    }
    return Promise.reject(error)
  }
)

// MCP client — separate instance with MCP API key
const mcpApi = axios.create({
  baseURL: '/mcp',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

mcpApi.interceptors.request.use((config) => {
  const mcpKey = localStorage.getItem('mcp_api_key') || 'dev-mcp-key'
  config.headers['X-MCP-API-Key'] = mcpKey
  return config
})

// --- Council ---
export const councilApi = {
  analyze: (query: string, context?: Record<string, unknown>) =>
    api.post('/council/analyze', { query, context }),
  streamUrl: () => `${API_BASE}/council/stream`,
  exportPdf: (sessionId: string) =>
    api.get(`/council/export/${sessionId}`, { responseType: 'blob' }),
}

// --- RAG ---
export const ragApi = {
  upload: (files: File[]) => {
    const formData = new FormData()
    files.forEach((f) => formData.append('files', f))
    return api.post('/rag/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  uploadUrl: (url: string, maxDepth?: number) =>
    api.post('/rag/upload-url', { url, max_depth: maxDepth ?? null }),
  query: (query: string, topK = 5) =>
    api.post('/rag/query', { query, top_k: topK }),
  graphQuery: (query: string) =>
    api.post('/rag/graph-query', { query }),
  hybridQuery: (query: string, topK = 5) =>
    api.post('/rag/hybrid-query', { query, top_k: topK }),
  collections: () => api.get('/rag/collections'),
  deleteCollection: (name: string) => api.delete(`/rag/collections/${name}`),
  documents: () => api.get('/rag/documents'),
  stats: () => api.get('/rag/stats'),
  health: () => api.get('/rag/health'),
}

// --- Risk ---
export const riskApi = {
  suppliers: () => api.get('/risk/suppliers'),
  supplier: (name: string) => api.get(`/risk/supplier/${name}`),
  supplierScore: (id: string) => api.get(`/risk/score/${id}`),
  heatmap: () => api.get('/risk/heatmap'),
  alerts: () => api.get('/risk/alerts'),
  assess: (supplier: string) => api.post('/risk/assess', { supplier }),
}

// --- Optimize ---
export const optimizeApi = {
  routes: (data: Record<string, unknown>) => api.post('/optimize/routes', data),
  inventory: (data: Record<string, unknown>) => api.post('/optimize/inventory', data),
}

// --- Ingest ---
export const ingestApi = {
  status: () => api.get('/ingest/status'),
  start: (source: string) => api.post('/ingest/start', { source }),
}

// --- Settings ---
export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data: Record<string, unknown>) => api.put('/settings', data),
}

// --- Health ---
export const healthApi = {
  check: () => api.get('/health'),
  ready: () => api.get('/ready'),
}

// --- Models ---
export const modelsApi = {
  list: () => api.get('/models/status'),
}

// --- MCP ---
export const mcpApiMethods = {
  listTools: () => mcpApi.get('/tools'),
  invoke: (tool: string, params: Record<string, unknown>) =>
    mcpApi.post(`/tools/${tool}/invoke`, params),
}

// --- Market (Real-Time Data) ---
export const marketApi = {
  ticker: () => api.get('/market/ticker'),
  company: (symbol: string) => api.get(`/market/company/${symbol}`),
  riskDashboard: () => api.get('/market/risk-dashboard'),
  brandIntel: () => api.get('/market/brand-intel'),
}

export { api, mcpApi }
export default api
