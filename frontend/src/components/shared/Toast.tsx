import { useState, useEffect, useCallback } from 'react'
import { clsx } from 'clsx'
import { X } from 'lucide-react'

type ToastType = 'success' | 'error' | 'info' | 'warning'

interface ToastItem {
  id: string
  type: ToastType
  message: string
}

const typeStyles: Record<ToastType, string> = {
  success: 'bg-success-green/10 border-success-green/30 text-success-green',
  error: 'bg-risk-red/10 border-risk-red/30 text-risk-red',
  info: 'bg-supply-blue/10 border-supply-blue/30 text-supply-blue',
  warning: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500',
}

// Simple toast container — can be replaced with shadcn toast later
let addToastFn: ((type: ToastType, message: string) => void) | null = null

export function toast(type: ToastType, message: string) {
  addToastFn?.(type, message)
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = Math.random().toString(36).slice(2)
    setToasts((prev) => [...prev, { id, type, message }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  useEffect(() => {
    addToastFn = addToast
    return () => { addToastFn = null }
  }, [addToast])

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={clsx('flex items-center gap-2 px-4 py-3 rounded-lg border animate-slide-in', typeStyles[t.type])}
        >
          <span className="flex-1 text-sm">{t.message}</span>
          <button onClick={() => removeToast(t.id)} className="shrink-0 hover:opacity-70">
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )
}
