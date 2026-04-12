import { Shield, TrendingUp, AlertTriangle, DollarSign } from 'lucide-react'

const stats = [
  { label: 'Risk Score', value: '72', icon: Shield, color: 'text-red-400' },
  { label: 'Active Disruptions', value: '3', icon: AlertTriangle, color: 'text-yellow-400' },
  { label: 'Predicted Savings', value: '$2.9M', icon: DollarSign, color: 'text-green-400' },
  { label: 'Council Runs', value: '12', icon: TrendingUp, color: 'text-blue-400' },
]

export default function Dashboard() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Supply Chain Dashboard</h1>
        <p className="text-gray-400 mt-1">Real-time risk monitoring & council insights</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">{label}</span>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <p className="text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
        <h2 className="text-lg font-semibold mb-4">Risk Heatmap</h2>
        <p className="text-gray-500">Interactive supplier risk visualization will appear here</p>
      </div>
    </div>
  )
}
