import { describe, it, expect, beforeEach } from 'vitest'
import { useSettingsStore } from '../settingsStore'

describe('settingsStore', () => {
  beforeEach(() => {
    useSettingsStore.getState().reset()
  })

  it('has correct default values', () => {
    const { settings } = useSettingsStore.getState()
    expect(settings.api_key).toBe('dev-key')
    expect(settings.theme).toBe('light')
    expect(settings.rag_chunk_size).toBe(512)
    expect(settings.response_verbosity).toBe('standard')
    expect(settings.font_size).toBe('medium')
    expect(settings.font_family).toBe('system')
    expect(settings.notifications_enabled).toBe(true)
    expect(settings.max_debate_rounds).toBe(3)
    expect(settings.stream_tokens).toBe(true)
    expect(settings.preferred_data_sources).toEqual(['firecrawl', 'finnhub', 'fred'])
    expect(settings.enable_web_scraping).toBe(true)
  })

  it('updates individual settings', () => {
    useSettingsStore.getState().updateSettings({ theme: 'dark' })
    expect(useSettingsStore.getState().settings.theme).toBe('dark')

    useSettingsStore.getState().updateSettings({ response_verbosity: 'detailed' })
    expect(useSettingsStore.getState().settings.response_verbosity).toBe('detailed')

    useSettingsStore.getState().updateSettings({ font_size: 'large' })
    expect(useSettingsStore.getState().settings.font_size).toBe('large')
  })

  it('updates multiple settings at once', () => {
    useSettingsStore.getState().updateSettings({
      theme: 'dark',
      font_size: 'small',
      notifications_sound: true,
    })
    const { settings } = useSettingsStore.getState()
    expect(settings.theme).toBe('dark')
    expect(settings.font_size).toBe('small')
    expect(settings.notifications_sound).toBe(true)
  })

  it('preserves unmodified settings during partial update', () => {
    const originalApiKey = useSettingsStore.getState().settings.api_key
    useSettingsStore.getState().updateSettings({ theme: 'dark' })
    expect(useSettingsStore.getState().settings.api_key).toBe(originalApiKey)
  })

  it('resets all settings to defaults', () => {
    useSettingsStore.getState().updateSettings({
      theme: 'dark',
      font_size: 'large',
      response_verbosity: 'concise',
      notifications_enabled: false,
    })
    useSettingsStore.getState().reset()
    const { settings } = useSettingsStore.getState()
    expect(settings.theme).toBe('light')
    expect(settings.font_size).toBe('medium')
    expect(settings.response_verbosity).toBe('standard')
    expect(settings.notifications_enabled).toBe(true)
  })

  it('loads settings from API data', () => {
    useSettingsStore.getState().loadFromApi({
      api_key: 'new-api-key',
      theme: 'dark',
      rag_chunk_size: 1024,
    })
    const { settings, isLoaded } = useSettingsStore.getState()
    expect(settings.api_key).toBe('new-api-key')
    expect(settings.theme).toBe('dark')
    expect(settings.rag_chunk_size).toBe(1024)
    expect(isLoaded).toBe(true)
  })

  it('updates preferred data sources order', () => {
    useSettingsStore.getState().updateSettings({
      preferred_data_sources: ['finnhub', 'fred', 'firecrawl'],
    })
    expect(useSettingsStore.getState().settings.preferred_data_sources).toEqual([
      'finnhub', 'fred', 'firecrawl',
    ])
  })

  it('toggles boolean settings', () => {
    expect(useSettingsStore.getState().settings.notifications_sound).toBe(false)
    useSettingsStore.getState().updateSettings({ notifications_sound: true })
    expect(useSettingsStore.getState().settings.notifications_sound).toBe(true)
    useSettingsStore.getState().updateSettings({ notifications_sound: false })
    expect(useSettingsStore.getState().settings.notifications_sound).toBe(false)
  })
})
