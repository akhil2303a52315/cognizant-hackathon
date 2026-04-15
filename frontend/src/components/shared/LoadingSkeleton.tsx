import { clsx } from 'clsx'

type Variant = 'card' | 'table' | 'message' | 'text'

interface LoadingSkeletonProps {
  variant?: Variant
  count?: number
  className?: string
}

function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3 animate-pulse shadow-card">
      <div className="h-4 bg-gray-200 rounded w-3/4" />
      <div className="h-3 bg-gray-100 rounded w-1/2" />
      <div className="h-3 bg-gray-100 rounded w-full" />
      <div className="h-3 bg-gray-100 rounded w-5/6" />
    </div>
  )
}

function SkeletonTable() {
  return (
    <div className="space-y-2 animate-pulse">
      <div className="h-8 bg-gray-100 rounded" />
      <div className="h-8 bg-gray-50 rounded" />
      <div className="h-8 bg-gray-50/60 rounded" />
      <div className="h-8 bg-gray-50/40 rounded" />
    </div>
  )
}

function SkeletonMessage() {
  return (
    <div className="flex gap-3 animate-pulse">
      <div className="w-8 h-8 bg-gray-200 rounded-full shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-3 bg-gray-200 rounded w-1/4" />
        <div className="h-3 bg-gray-100 rounded w-full" />
        <div className="h-3 bg-gray-100 rounded w-3/4" />
      </div>
    </div>
  )
}

function SkeletonText() {
  return (
    <div className="space-y-2 animate-pulse">
      <div className="h-3 bg-gray-200 rounded w-full" />
      <div className="h-3 bg-gray-100 rounded w-5/6" />
      <div className="h-3 bg-gray-100 rounded w-4/6" />
    </div>
  )
}

const variantMap: Record<Variant, () => JSX.Element> = {
  card: SkeletonCard,
  table: SkeletonTable,
  message: SkeletonMessage,
  text: SkeletonText,
}

export default function LoadingSkeleton({ variant = 'card', count = 1, className }: LoadingSkeletonProps) {
  const Component = variantMap[variant]
  return (
    <div className={clsx('space-y-3', className)}>
      {Array.from({ length: count }, (_, i) => (
        <Component key={i} />
      ))}
    </div>
  )
}
