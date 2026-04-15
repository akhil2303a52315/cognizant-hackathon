import { clsx } from 'clsx'

type Status = 'online' | 'offline' | 'error' | 'loading'

interface StatusBadgeProps {
  status: Status
  label?: string
  size?: 'sm' | 'md'
}

const statusStyles: Record<Status, string> = {
  online: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  offline: 'bg-gray-100 text-gray-500 border-gray-200',
  error: 'bg-red-50 text-red-700 border-red-200',
  loading: 'bg-amber-50 text-amber-700 border-amber-200 animate-pulse',
}

const dotStyles: Record<Status, string> = {
  online: 'bg-emerald-500',
  offline: 'bg-gray-400',
  error: 'bg-red-500',
  loading: 'bg-amber-500 animate-pulse',
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
