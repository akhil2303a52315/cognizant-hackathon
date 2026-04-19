/** Zustand persist key — must match settingsStore `persist({ name })` */
const SETTINGS_STORAGE_KEY = 'supplychaingpt-settings'

function readFromPersistedSettings(): string | null {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as { state?: { settings?: { api_key?: string } } }
    const k = parsed?.state?.settings?.api_key
    if (typeof k === 'string' && k.trim().length > 0) return k.trim()
  } catch {
    /* ignore corrupt localStorage */
  }
  return null
}

/** Same key the Settings page edits (Zustand persist), then legacy `api_key`, then default. */
export function getClientApiKey(): string {
  const legacy = localStorage.getItem('api_key')?.trim()
  return readFromPersistedSettings() ?? (legacy || 'dev-key')
}

export function getClientMcpApiKey(): string {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as { state?: { settings?: { mcp_api_key?: string } } }
      const k = parsed?.state?.settings?.mcp_api_key
      if (typeof k === 'string' && k.trim().length > 0) return k.trim()
    }
  } catch {
    /* ignore */
  }
  const legacy = localStorage.getItem('mcp_api_key')?.trim()
  return legacy || 'dev-mcp-key'
}
