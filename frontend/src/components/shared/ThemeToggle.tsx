import { Moon, Sun } from 'lucide-react'
import { useSettingsStore } from '@/store/settingsStore'

export default function ThemeToggle() {
  const { settings, updateSettings } = useSettingsStore()
  const isDark = settings.theme === 'dark'

  const toggle = () => {
    const next = isDark ? 'light' : 'dark'
    updateSettings({ theme: next })
    document.documentElement.classList.toggle('dark', next === 'dark')
  }

  return (
    <button
      onClick={toggle}
      className="p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </button>
  )
}
