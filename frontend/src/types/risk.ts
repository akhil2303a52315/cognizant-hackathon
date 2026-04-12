export interface SupplierRisk {
  supplier: string
  risk_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  categories: RiskCategory[]
  last_updated: string
}

export interface RiskCategory {
  name: string
  score: number
  trend: 'improving' | 'stable' | 'declining'
  factors: string[]
}

export interface RiskHeatmap {
  suppliers: SupplierRisk[]
  matrix: RiskMatrixCell[]
}

export interface RiskMatrixCell {
  supplier: string
  category: string
  score: number
}

export interface RiskScore {
  overall: number
  financial: number
  operational: number
  geopolitical: number
  environmental: number
  reputational: number
}

export interface RiskAlert {
  id: string
  supplier: string
  alert_type: string
  severity: 'info' | 'warning' | 'critical'
  message: string
  timestamp: string
  acknowledged: boolean
}

export interface RiskAssessment {
  supplier: string
  risk_score: RiskScore
  alerts: RiskAlert[]
  recommendations: string[]
}
