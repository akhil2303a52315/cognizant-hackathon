import { Link } from 'react-router-dom'
import { Shield } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <Shield className="w-16 h-16 text-gray-600 mb-4" />
      <h1 className="text-4xl font-bold text-gray-300 mb-2">404</h1>
      <p className="text-gray-500 mb-6">Page not found</p>
      <Link
        to="/"
        className="px-4 py-2 bg-supply-blue rounded-lg text-white hover:bg-supply-blue-dark transition-colors"
      >
        Back to Dashboard
      </Link>
    </div>
  )
}
