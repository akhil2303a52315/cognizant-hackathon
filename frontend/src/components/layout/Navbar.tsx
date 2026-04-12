import { Link, useLocation } from 'react-router-dom'
import { Shield, MessageSquare, Flame, Eye } from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Shield },
  { path: '/chat', label: 'Council Chat', icon: MessageSquare },
  { path: '/debate', label: 'Debate', icon: Flame },
  { path: '/brand', label: 'Brand Control', icon: Eye },
]

export default function Navbar() {
  const location = useLocation()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-900/80 backdrop-blur-md border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <Shield className="w-8 h-8 text-blue-500" />
          <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            SupplyChainGPT
          </span>
        </Link>
        <div className="flex items-center gap-1">
          {navItems.map(({ path, label, icon: Icon }) => {
            const active = location.pathname === path
            return (
              <Link
                key={path}
                to={path}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  active
                    ? 'bg-blue-500/10 text-blue-400'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
