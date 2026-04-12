import { clsx } from 'clsx'

interface ConfidenceBarProps {
  value: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const colorMap = (value: number) => {
  if (value >= 80) return 'bg-success-green'
  if (value >= 60) return 'bg-supply-blue'
  if (value >= 40) return 'bg-yellow-500'
  return 'bg-risk-red'
}

const sizeMap = { sm: 'h-1.5', md: 'h-2.5', lg: 'h-4' }

export default function ConfidenceBar({ value, size = 'md', showLabel = true }: ConfidenceBarProps) {
  const clamped = Math.max(0, Math.min(100, value))
  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={clsx('rounded-full transition-all duration-500 ease-out', colorMap(clamped), sizeMap[size])}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className={clsx('text-xs font-mono min-w-[3ch]', clamped >= 80 ? 'text-success-green' : clamped >= 40 ? 'text-yellow-500' : 'text-risk-red')}>
          {clamped}%
        </span>
      )}
    </div>
  )
}
