import { clsx } from 'clsx'

interface ConfidenceBarProps {
  value: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const colorMap = (value: number) => {
  if (value >= 80) return 'bg-emerald-500'
  if (value >= 60) return 'bg-blue-500'
  if (value >= 40) return 'bg-amber-500'
  return 'bg-red-500'
}

const sizeMap = { sm: 'h-1.5', md: 'h-2.5', lg: 'h-4' }

export default function ConfidenceBar({ value, size = 'md', showLabel = true }: ConfidenceBarProps) {
  const clamped = Math.max(0, Math.min(100, value))
  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={clsx('rounded-full transition-all duration-500 ease-out', colorMap(clamped), sizeMap[size])}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className={clsx('text-xs font-mono min-w-[3ch]', clamped >= 80 ? 'text-emerald-600' : clamped >= 40 ? 'text-amber-600' : 'text-red-600')}>
          {clamped}%
        </span>
      )}
    </div>
  )
}
