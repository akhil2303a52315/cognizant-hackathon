import { clsx } from 'clsx'

type Status = 'online' | 'offline' | 'error' | 'loading'

interface StatusBadgeProps {
  status: Status
  label?: string
  size?: 'sm' | 'md'
}

const statusStyles: Record<Status, string> = {
  online: 'bg-success-green/20 text-success-green border-success-green/30',
  offline: 'bg-gray-600/20 text-gray-400 border-gray-600/30',
  error: 'bg-risk-red/20 text-risk-red border-risk-red/30',
  loading: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30 animate-pulse',
}

const dotStyles: Record<Status, string> = {
  online: 'bg-success-green',
  offline: 'bg-gray-500',
  error: 'bg-risk-red',
  loading: 'bg-yellow-500 animate-pulse',
}

export default function StatusBadge({ status, label, size = 'md' }: StatusBadgeProps) {
  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 rounded-full border font-medium',
      statusStyles[status],
      size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
    )}>
      <span className={clsx('rounded-full', dotStyles[status], size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2')} />
      {label || status}
    </span>
  )
}
