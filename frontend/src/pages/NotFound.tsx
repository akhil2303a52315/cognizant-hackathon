import { Link } from 'react-router-dom'
import { Shield, ArrowLeft } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <div className="animate-float">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center mb-6">
          <Shield className="w-10 h-10 text-gray-400" />
        </div>
      </div>
      <h1 className="text-6xl font-bold text-gradient mb-2">404</h1>
      <p className="text-gray-500 mb-8 text-lg">Page not found</p>
      <Link
        to="/"
        className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 rounded-xl text-white hover:bg-blue-700 transition-all duration-200 shadow-sm hover:shadow-md"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>
    </div>
  )
}
