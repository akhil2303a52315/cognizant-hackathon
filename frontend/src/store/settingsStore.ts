import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppSettings {
  api_key: string
  mcp_api_key: string
  theme: 'dark' | 'light'
  sidebar_collapsed: boolean
  rag_chunk_size: number
  rag_chunk_overlap: number
  rag_top_k: number
  mcp_rate_limit: number
}

interface SettingsState {
  settings: AppSettings
  isLoaded: boolean
  updateSettings: (partial: Partial<AppSettings>) => void
  loadFromApi: (data: Record<string, unknown>) => void
  reset: () => void
}

const defaultSettings: AppSettings = {
  api_key: 'dev-key',
  mcp_api_key: 'dev-mcp-key',
  theme: 'light',
  sidebar_collapsed: false,
  rag_chunk_size: 512,
  rag_chunk_overlap: 50,
  rag_top_k: 5,
  mcp_rate_limit: 30,
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      isLoaded: false,

      updateSettings: (partial) =>
        set((state) => ({
          settings: { ...state.settings, ...partial },
        })),

      loadFromApi: (data) =>
        set((state) => ({
          settings: { ...state.settings, ...data },
          isLoaded: true,
        })),

      reset: () => set({ settings: defaultSettings, isLoaded: false }),
    }),
    { name: 'supplychaingpt-settings' }
  )
)
