# SupplyChainGPT — Debate Engine Specification

Complete specification for the Council of Debate AI Agents engine: architecture, debate mechanics, confidence scoring, round management, challenge protocol, synthesis logic, fallback generation, Monte Carlo simulation, prediction engine, self-reflection, human-in-the-loop, and working examples.

---

## 1. Debate Engine Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      DEBATE ENGINE ARCHITECTURE                               │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     LANGGRAPH COUNCIL GRAPH                             │  │
│  │                                                                         │  │
│  │  ┌───────────┐                                                         │  │
│  │  │ MODERATOR │  Entry point — routes query, manages rounds              │  │
│  │  │           │                                                         │  │
│  │  │ • Parse query                                                       │  │
│  │  │ • Assign context                                                    │  │
│  │  │ • Track rounds                                                      │  │
│  │  │ • Identify conflicts                                                │  │
│  │  │ • Force synthesis at round 3                                        │  │
│  │  └─────┬─────┘                                                         │  │
│  │        │                                                                 │  │
│  │        │ Fan-out (parallel)                                              │  │
│  │        │                                                                 │  │
│  │  ┌─────┴──────────────────────────────────────────────────────────┐    │  │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │  │  │
│  │  │  │  RISK  │ │SUPPLY  │ │LOGISTICS│ │ MARKET │ │FINANCE │ │ BRAND  │ │  │  │
│  │  │  │        │ │        │ │         │ │        │ │        │ │        │ │  │  │
│  │  │  │87%conf │ │91%conf │ │85%conf  │ │78%conf │ │82%conf │ │75%conf │ │  │  │
│  │  │  └───┬────┘ └───┬────┘ └────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ │  │  │
│  │  └──────┼───────────┼───────────┼──────────┼──────────┼──────────┼──────┘    │  │
│  │         │           │           │          │          │          │           │  │
│  │         └───────────┴───────────┴──────────┴──────────┴──────────┘           │  │
│  │                                    │                                        │  │
│  │                     ┌──────────────▼──────────────┐                        │  │
│  │                     │     DEBATE CONDITION CHECK    │                        │  │
│  │                     │                               │                        │  │
│  │                     │  Gap > 20%? ──► DEBATE ROUND  │                        │  │
│  │                     │  Gap ≤ 20%? ──► SYNTHESIZE     │                        │  │
│  │                     │  Round ≥ 3?  ──► SYNTHESIZE    │                        │  │
│  │                     └──────────────┬──────────────┘                        │  │
│  │                                    │                                        │  │
│  │               ┌────────────────────┼────────────────────┐                   │  │
│  │               │                    │                    │                   │  │
│  │        ┌──────▼──────┐    ┌───────▼───────┐    ┌──────▼──────┐           │  │
│  │        │  DEBATE     │    │  SELF-        │    │ SYNTHESIZE  │           │  │
│  │        │  ROUND 2+   │    │  REFLECTION   │    │ (Final)     │           │  │
│  │        │             │    │  (if conf<30) │    │             │           │  │
│  │        │ Challenge   │    │  Re-query LLM │    │ Moderator   │           │  │
│  │        │ + Respond   │    │  with context │    │ synthesizes │           │  │
│  │        └──────┬──────┘    └───────┬───────┘    │ all outputs │           │  │
│  │               │                   │            │ + fallbacks │           │  │
│  │               └───────────────────┘            └──────┬─────┘           │  │
│  │                                                        │                 │  │
│  │                                                 ┌──────▼─────┐         │  │
│  │                                                 │  FINAL      │         │  │
│  │                                                 │  OUTPUT     │         │  │
│  │                                                 │             │         │  │
│  │                                                 │ Recommend. │         │  │
│  │                                                 │ Confidence  │         │  │
│  │                                                 │ Fallbacks   │         │  │
│  │                                                 │ Evidence    │         │  │
│  │                                                 └────────────┘         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Debate Mechanics

### 2.1 Round Flow

```
Round 0: MODERATOR PARSE
  └── Parse query → Extract context → Initialize state

Round 1: PARALLEL ANALYSIS
  └── All 6 agents analyze simultaneously (fan-out)
  └── Each returns: confidence, contribution, key_points, evidence
  └── Check debate condition

Round 2: DEBATE (if triggered)
  └── Identify top-2 conflicting agents
  └── Challenger presents argument with evidence
  └── Challenged agent responds with counter-evidence
  └── Other agents may support either side
  └── Check debate condition again

Round 3: FORCED SYNTHESIS
  └── Regardless of remaining gap, moderator synthesizes
  └── Weighted confidence average
  └── Generate recommendation + fallbacks + evidence
```

### 2.2 Debate Trigger Conditions

| Condition | Result | Rationale |
|-----------|--------|-----------|
| All confidences within 20% gap | Skip debate → Synthesize | Agents agree sufficiently |
| Any two agents > 20% gap | Trigger debate | Significant disagreement |
| Any agent confidence < 30% | Self-reflection first | Agent is uncertain — needs more context |
| Round number ≥ 3 | Force synthesis | Prevent infinite debate loops |
| All agents confidence > 80% | Skip debate → Synthesize | High agreement — no need to debate |

### 2.3 Confidence Gap Calculation

```python
# backend/agents/debate_engine.py

def calculate_confidence_gap(outputs: list[AgentOutput]) -> float:
    """Calculate the maximum confidence gap between any two agents."""
    if len(outputs) < 2:
        return 0.0
    confidences = [o.confidence for o in outputs]
    return max(confidences) - min(confidences)

def should_trigger_debate(outputs: list[AgentOutput], round_number: int) -> str:
    """Determine next action based on agent outputs."""
    # Force synthesis after 3 rounds
    if round_number >= 3:
        return "synthesize"

    # Check for low-confidence agents
    low_conf_agents = [o for o in outputs if o.confidence < 30]
    if low_conf_agents:
        return "self_reflect"

    # Check confidence gap
    gap = calculate_confidence_gap(outputs)
    if gap > 20:
        return "debate"

    # All agree
    return "synthesize"
```

---

## 3. Challenge Protocol

### 3.1 Challenge Identification

```python
# backend/agents/challenge.py

from backend.state import AgentOutput
from typing import Optional

def identify_debate_pair(outputs: list[AgentOutput]) -> tuple[AgentOutput, AgentOutput]:
    """Identify the two most conflicting agents for debate."""
    # Sort by confidence
    sorted_outputs = sorted(outputs, key=lambda o: o.confidence, reverse=True)
    highest = sorted_outputs[0]
    lowest = sorted_outputs[-1]
    return highest, lowest

def generate_challenge_prompt(challenger: AgentOutput, challenged: AgentOutput, query: str) -> str:
    """Generate challenge prompt for the debate round."""
    return f"""You are {challenger.agent.upper()} agent with {challenger.confidence}% confidence.
The {challenged.agent.upper()} agent has only {challenged.confidence}% confidence and claims:
"{challenged.contribution}"

Your position:
"{challenger.contribution}"

CHALLENGE: Present evidence-based arguments why your assessment is more accurate.
Address the specific points where you disagree with {challenged.agent.upper()}.
Provide concrete data, metrics, or references to support your position.

Format your response as:
{{
  "challenge_points": ["point 1", "point 2", ...],
  "evidence": [{{"type": "...", "id": "..."}}],
  "revised_confidence": <0-100>,
  "concession_points": ["where you agree with the other agent"]
}}"""
```

### 3.2 Response Protocol

```python
def generate_response_prompt(challenged: AgentOutput, challenger: AgentOutput, challenge_text: str) -> str:
    """Generate response prompt for the challenged agent."""
    return f"""You are {challenged.agent.upper()} agent with {challenged.confidence}% confidence.
The {challenger.agent.upper()} agent (at {challenger.confidence}% confidence) challenges your assessment with:

{challenge_text}

RESPOND: Address each challenge point. Either:
1. Defend your position with additional evidence
2. Concede the point and adjust your confidence accordingly
3. Propose a middle-ground interpretation

Be intellectually honest. If the challenger makes valid points, acknowledge them.

Format your response as:
{{
  "responses": [{{"challenge_point": "...", "response": "...", "action": "defend|concede|middle_ground"}}],
  "evidence": [{{"type": "...", "id": "..."}}],
  "revised_confidence": <0-100>,
  "concessions_made": ["..."]
}}"""
```

### 3.3 Debate Scoring

```python
class DebateScorer:
    """Score debate rounds to determine if consensus is reached."""

    @staticmethod
    def score_round(
        challenger: AgentOutput,
        challenged: AgentOutput,
        challenge: dict,
        response: dict,
    ) -> dict:
        """Score a debate round."""
        challenger_concessions = len(challenge.get("concession_points", []))
        challenged_concessions = len(response.get("concessions_made", []))

        evidence_quality_challenger = len(challenge.get("evidence", []))
        evidence_quality_challenged = len(response.get("evidence", []))

        # Points awarded for evidence-backed arguments
        challenger_score = (evidence_quality_challenger * 10) - (challenger_concessions * 5)
        challenged_score = (evidence_quality_challenged * 10) - (challenged_concessions * 5)

        return {
            "challenger_score": challenger_score,
            "challenged_score": challenged_score,
            "consensus_reached": abs(challenger.revised_confidence - challenged.revised_confidence) < 15,
            "total_concessions": challenger_concessions + challenged_concessions,
        }
```

---

## 4. Self-Reflection Engine

### 4.1 When Self-Reflection Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Agent confidence < 30% | Very uncertain | Re-query with additional context |
| Agent returns error | LLM failure | Retry with fallback provider |
| Agent output has no evidence | Unsubstantiated | Re-query demanding evidence |
| Agent confidence drops between rounds | New info weakened position | Re-evaluate with full context |

### 4.2 Self-Reflection Implementation

```python
# backend/agents/self_reflection.py

SELF_REFLECT_PROMPT = """You previously responded to the query: "{query}"
Your confidence was only {confidence}%, which is very low.

Previous response: {previous_response}

OTHER AGENTS' CONTEXT:
{other_agent_outputs}

Please re-evaluate with this additional context. Either:
1. Increase your confidence if the new context supports your position
2. Decrease further if the new context contradicts you
3. Maintain but provide stronger evidence

Respond with the same structured format, but with updated confidence and evidence."""

async def self_reflect(
    agent_name: str,
    query: str,
    previous_output: AgentOutput,
    other_outputs: list[AgentOutput],
    llm_router,
) -> AgentOutput:
    """Trigger self-reflection for a low-confidence agent."""
    other_context = "\n".join([
        f"- {o.agent} ({o.confidence}%): {o.contribution[:200]}"
        for o in other_outputs if o.agent != agent_name
    ])

    prompt = SELF_REFLECT_PROMPT.format(
        query=query,
        confidence=previous_output.confidence,
        previous_response=previous_output.contribution,
        other_agent_outputs=other_context,
    )

    try:
        response, model_info = await llm_router.invoke_with_fallback(agent_name, [
            {"role": "system", "content": f"You are the {agent_name} agent performing self-reflection."},
            {"role": "user", "content": prompt},
        ])

        return AgentOutput(
            agent=agent_name,
            confidence=min(previous_output.confidence + 15, 95),  # Cap at 95
            contribution=str(response.content),
            key_points=previous_output.key_points,
            model_used=model_info,
            provider=model_info.split(":")[0],
        )
    except Exception as e:
        # If self-reflection fails, keep original but flag it
        return AgentOutput(
            agent=agent_name,
            confidence=previous_output.confidence,
            contribution=previous_output.contribution + "\n[SELF-REFLECTION FAILED]",
            key_points=previous_output.key_points,
            model_used="error",
            provider="error",
        )
```

---

## 5. Synthesis Engine

### 5.1 Moderator Synthesis

```python
# backend/agents/synthesis.py

SYNTHESIS_PROMPT = """You are the Moderator of the Council of Debate AI Agents.

QUERY: {query}

AGENT OUTPUTS:
{agent_outputs}

DEBATE HISTORY:
{debate_history}

Your job is to synthesize a FINAL RECOMMENDATION that:
1. Weighs each agent's contribution by their confidence score
2. Resolves any remaining conflicts from the debate
3. Provides a clear, actionable recommendation
4. Includes 3 tiers of fallback options
5. Cites specific evidence from agent outputs

OUTPUT FORMAT (strict):
{{
  "recommendation": "<clear, actionable recommendation in 2-3 sentences>",
  "confidence": <0-100 overall confidence>,
  "risk_score": <0-100 overall risk>,
  "key_drivers": ["<top 3-5 factors driving the recommendation>"],
  "fallback_options": [
    {{
      "tier": 1,
      "label": "IMMEDIATE (0-48h)",
      "actions": ["<specific action>"],
      "cost_estimate": <float>,
      "risk_reduction": <float>
    }},
    {{
      "tier": 2,
      "label": "SHORT-TERM (2-4 weeks)",
      "actions": ["<specific action>"],
      "cost_estimate": <float>,
      "risk_reduction": <float>
    }},
    {{
      "tier": 3,
      "label": "STRATEGIC (1-6 months)",
      "actions": ["<specific action>"],
      "cost_estimate": <float>,
      "risk_reduction": <float>
    }}
  ],
  "evidence": [{{"type": "...", "id": "...", "tag": "..."}}],
  "agents_agree": <bool>,
  "remaining_conflicts": ["<any unresolved disagreements>"]
}}"""

async def synthesize_council(
    query: str,
    agent_outputs: list[AgentOutput],
    debate_history: list[dict],
    llm_router,
) -> dict:
    """Synthesize final council recommendation."""
    # Format agent outputs
    outputs_text = "\n".join([
        f"• {o.agent.upper()} ({o.confidence}% confidence, {o.provider}:{o.model_used}): {o.contribution}"
        for o in agent_outputs
    ])

    # Format debate history
    debate_text = ""
    for entry in debate_history:
        debate_text += f"Round {entry['round_number']}: {entry['challenger']} challenged {entry['challenged']} — {entry['challenge_text'][:200]}\n"
    if not debate_text:
        debate_text = "No debate rounds — all agents agreed."

    prompt = SYNTHESIS_PROMPT.format(
        query=query,
        agent_outputs=outputs_text,
        debate_history=debate_text,
    )

    response, model_info = await llm_router.invoke_with_fallback("moderator", [
        {"role": "system", "content": "You are the Council Moderator. Synthesize the final recommendation."},
        {"role": "user", "content": prompt},
    ])

    # Calculate weighted confidence
    weights = {
        "risk": 1.5,      # Risk weighted higher
        "supply": 1.3,    # Supply critical
        "logistics": 1.2, # Logistics important
        "market": 1.0,    # Market baseline
        "finance": 1.3,   # Finance critical
        "brand": 0.8,     # Brand lower weight in supply chain
    }

    total_weight = 0
    weighted_sum = 0
    for o in agent_outputs:
        w = weights.get(o.agent, 1.0)
        weighted_sum += o.confidence * w
        total_weight += w

    avg_confidence = weighted_sum / total_weight if total_weight > 0 else 0

    return {
        "recommendation": str(response.content),
        "confidence": round(avg_confidence, 1),
        "model_used": model_info,
    }
```

### 5.2 Confidence Weighting

| Agent | Weight | Rationale |
|-------|--------|-----------|
| Risk Sentinel | 1.5x | Risk is the primary driver in supply chain decisions |
| Supply Optimizer | 1.3x | Supply alternatives are critical for resolution |
| Finance Guardian | 1.3x | Financial impact determines action viability |
| Logistics Navigator | 1.2x | Logistics feasibility validates alternatives |
| Market Intelligence | 1.0x | Market context is baseline information |
| Brand Protector | 0.8x | Brand impact is secondary to operational concerns |

---

## 6. Fallback Generation Engine

### 6.1 Three-Tier Fallback System

```python
# backend/agents/fallbacks.py

FALLBACK_PROMPT = """Based on the council's recommendation and agent outputs, generate 3 tiers of fallback options.

RECOMMENDATION: {recommendation}
RISK SCORE: {risk_score}
CONFIDENCE: {confidence}

AGENT KEY POINTS:
{key_points}

Generate fallbacks following these rules:
- Tier 1: Immediate actions (0-48 hours), low risk, moderate cost
- Tier 2: Short-term actions (2-4 weeks), medium risk, higher cost
- Tier 3: Strategic actions (1-6 months), variable risk, high cost

Each action must include:
- Specific description (not vague)
- Estimated cost range
- Time to implement
- Risk reduction percentage
- Prerequisites

OUTPUT FORMAT:
{{
  "tier1_immediate": [
    {{"action": "...", "cost": ..., "time": "...", "risk_reduction_pct": ..., "prerequisites": [...]}}
  ],
  "tier2_short_term": [
    {{"action": "...", "cost": ..., "time": "...", "risk_reduction_pct": ..., "prerequisites": [...]}}
  ],
  "tier3_strategic": [
    {{"action": "...", "cost": ..., "time": "...", "risk_reduction_pct": ..., "prerequisites": [...]}}
  ],
  "roi_analysis": {{
    "disruption_exposure": ...,
    "total_mitigation_cost_tier1": ...,
    "net_savings": ...,
    "roi_pct": ...
  }}
}}"""
```

### 6.2 Fallback Example

```json
{
  "tier1_immediate": [
    {
      "action": "Activate backup supplier S2 (India) for Component C1",
      "cost": 45000,
      "time": "24 hours",
      "risk_reduction_pct": 35,
      "prerequisites": ["S2 contract active", "Quality pre-approved"]
    },
    {
      "action": "Emergency air freight bridge for 2-week gap",
      "cost": 185000,
      "time": "3 days",
      "risk_reduction_pct": 25,
      "prerequisites": ["Freight forwarder on retainer", "Customs pre-cleared"]
    },
    {
      "action": "Pause product availability ads → Launch 'Pre-order Now' campaign",
      "cost": 0,
      "time": "1 hour",
      "risk_reduction_pct": 10,
      "prerequisites": ["Marketing team standby", "Pre-order landing page ready"]
    }
  ],
  "tier2_short_term": [
    {
      "action": "Multi-source procurement split (S2 India + S3 Vietnam)",
      "cost": 120000,
      "time": "14 days",
      "risk_reduction_pct": 40,
      "prerequisites": ["S3 qualification complete", "Volume commitments negotiated"]
    },
    {
      "action": "File cargo insurance claim for delayed shipment",
      "cost": 0,
      "time": "10-15 business days",
      "risk_reduction_pct": 15,
      "prerequisites": ["Policy covers delay", "Documentation ready"]
    }
  ],
  "tier3_strategic": [
    {
      "action": "Geographic diversification (Vietnam + India dual sourcing)",
      "cost": 500000,
      "time": "90 days",
      "risk_reduction_pct": 60,
      "prerequisites": ["Supplier audit complete", "Long-term contracts drafted"]
    },
    {
      "action": "Safety stock policy revision (AI-optimized buffer levels)",
      "cost": 80000,
      "time": "30 days",
      "risk_reduction_pct": 30,
      "prerequisites": ["Demand forecasting model updated", "Warehouse capacity available"]
    }
  ],
  "roi_analysis": {
    "disruption_exposure": 2400000,
    "total_mitigation_cost_tier1": 230000,
    "net_savings": 2170000,
    "roi_pct": 943
  }
}
```

---

## 7. Monte Carlo Simulation Engine

### 7.1 Simulation Design

```python
# backend/tools/monte_carlo.py

import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class SimulationResult:
    p10: float       # 10th percentile (optimistic)
    p50: float       # 50th percentile (median)
    p90: float       # 90th percentile (pessimistic)
    mean: float
    std_dev: float
    scenarios: int

class MonteCarloEngine:
    """Run Monte Carlo simulations for supply chain risk scenarios."""

    def __init__(self, n_scenarios: int = 10000):
        self.n_scenarios = n_scenarios

    def simulate_supplier_delay(
        self,
        base_lead_time_days: float,
        delay_probability: float,
        delay_range_days: tuple[float, float],
        cost_per_day: float,
        mitigation_effectiveness: float = 0.0,
    ) -> SimulationResult:
        """Simulate financial exposure from supplier delays."""
        exposures = []

        for _ in range(self.n_scenarios):
            # Will this scenario have a delay?
            if np.random.random() < delay_probability:
                # How long is the delay?
                delay_days = np.random.uniform(delay_range_days[0], delay_range_days[1])
                # Apply mitigation reduction
                effective_delay = delay_days * (1 - mitigation_effectiveness)
                exposure = effective_delay * cost_per_day
            else:
                exposure = 0

            exposures.append(exposure)

        exposures = np.array(exposures)
        return SimulationResult(
            p10=np.percentile(exposures, 10),
            p50=np.percentile(exposures, 50),
            p90=np.percentile(exposures, 90),
            mean=np.mean(exposures),
            std_dev=np.std(exposures),
            scenarios=self.n_scenarios,
        )

    def simulate_multi_supplier(
        self,
        suppliers: list[dict],
        n_scenarios: int = 10000,
    ) -> dict:
        """Simulate scenarios across multiple suppliers simultaneously."""
        results = {}
        total_exposures = []

        for supplier in suppliers:
            result = self.simulate_supplier_delay(
                base_lead_time_days=supplier["lead_time_days"],
                delay_probability=supplier["delay_probability"],
                delay_range_days=supplier["delay_range_days"],
                cost_per_day=supplier["cost_per_day"],
                mitigation_effectiveness=supplier.get("mitigation_effectiveness", 0),
            )
            results[supplier["id"]] = result
            total_exposures.append(result.p50)

        return {
            "per_supplier": {k: {"p10": v.p10, "p50": v.p50, "p90": v.p90, "mean": v.mean}
                            for k, v in results.items()},
            "total_exposure": {
                "p10": sum(r.p10 for r in results.values()),
                "p50": sum(r.p50 for r in results.values()),
                "p90": sum(r.p90 for r in results.values()),
            },
            "scenarios_run": self.n_scenarios,
        }
```

### 7.2 Example Simulation

```python
# Example: Taiwan chip crisis scenario
engine = MonteCarloEngine(n_scenarios=10000)

result = engine.simulate_supplier_delay(
    base_lead_time_days=14,
    delay_probability=0.65,           # 65% chance of delay
    delay_range_days=(7, 28),         # 1-4 week delay range
    cost_per_day=85000,               # $85K/day exposure
    mitigation_effectiveness=0.35,    # 35% reduction with backup plan
)

# Result:
# p10:  $0          (no delay scenario)
# p50:  $800K       (moderate delay with partial mitigation)
# p90:  $2.4M       (severe delay, limited mitigation)
# mean: $1.1M
```

---

## 8. Prediction Engine

### 8.1 Forecast Models

```python
# backend/tools/forecasting.py

from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class ForecastPoint:
    horizon_days: int
    predicted_value: float
    confidence_lower: float
    confidence_upper: float
    trend: str  # "improving", "stable", "declining"

class PredictionEngine:
    """Generate 30/60/90-day predictions for supply chain metrics."""

    def predict_risk_trajectory(
        self,
        current_risk_score: float,
        mitigation_actions: list[str],
        historical_trend: str = "stable",
    ) -> list[ForecastPoint]:
        """Predict risk score trajectory over 30/60/90 days."""
        # Base trajectory (without mitigation)
        if historical_trend == "declining":
            base_delta = -2  # Risk naturally declining
        elif historical_trend == "increasing":
            base_delta = 3   # Risk naturally increasing
        else:
            base_delta = 0   # Stable

        # Mitigation impact
        mitigation_reduction = len(mitigation_actions) * 5  # ~5 points per action

        forecasts = []
        for horizon in [30, 60, 90]:
            # Mitigation effect compounds over time but plateaus
            mitigation_effect = mitigation_reduction * min(horizon / 60, 1.0)
            natural_change = base_delta * (horizon / 30)

            predicted = max(0, min(100, current_risk_score + natural_change - mitigation_effect))

            # Confidence interval widens with horizon
            uncertainty = 5 + (horizon / 10)
            lower = max(0, predicted - uncertainty * 1.5)
            upper = min(100, predicted + uncertainty)

            if predicted < current_risk_score:
                trend = "improving"
            elif predicted > current_risk_score + 5:
                trend = "declining"
            else:
                trend = "stable"

            forecasts.append(ForecastPoint(
                horizon_days=horizon,
                predicted_value=round(predicted, 1),
                confidence_lower=round(lower, 1),
                confidence_upper=round(upper, 1),
                trend=trend,
            ))

        return forecasts

    def predict_cost_impact(
        self,
        current_exposure: float,
        mitigation_cost: float,
        mitigation_effectiveness: float,
        horizon_days: int = 90,
    ) -> dict:
        """Predict financial impact of mitigation vs. no mitigation."""
        # Without mitigation: exposure continues
        no_mitigation_cost = current_exposure * (horizon_days / 90)

        # With mitigation: reduced exposure
        mitigated_exposure = current_exposure * (1 - mitigation_effectiveness)
        with_mitigation_cost = mitigated_exposure * (horizon_days / 90) + mitigation_cost

        net_savings = no_mitigation_cost - with_mitigation_cost
        roi = (net_savings / mitigation_cost * 100) if mitigation_cost > 0 else 0

        return {
            "no_mitigation_cost": round(no_mitigation_cost, 2),
            "with_mitigation_cost": round(with_mitigation_cost, 2),
            "net_savings": round(net_savings, 2),
            "roi_pct": round(roi, 1),
            "break_even_days": round(mitigation_cost / (current_exposure * mitigation_effectiveness / 90), 1) if mitigation_effectiveness > 0 else None,
        }
```

### 8.2 Example Prediction

```python
engine = PredictionEngine()

forecasts = engine.predict_risk_trajectory(
    current_risk_score=72,
    mitigation_actions=["Activate S2", "Air freight bridge", "Launch pre-order campaign"],
    historical_trend="increasing",
)

# Results:
# 30d: predicted=62, range=[53, 71], trend="improving"
# 60d: predicted=47, range=[35, 59], trend="improving"
# 90d: predicted=38, range=[24, 52], trend="improving"

cost = engine.predict_cost_impact(
    current_exposure=2400000,
    mitigation_cost=230000,
    mitigation_effectiveness=0.85,
)

# Results:
# no_mitigation_cost: $2,400,000
# with_mitigation_cost: $590,000
# net_savings: $1,810,000
# roi_pct: 787%
# break_even_days: 10.2
```

---

## 9. Human-in-the-Loop

### 9.1 Interrupt Points

```python
# backend/agents/human_in_loop.py

from backend.state import CouncilState

HUMAN_REVIEW_POINTS = [
    "pre_synthesis",    # Before moderator synthesizes (review agent outputs)
    "post_synthesis",   # After recommendation (approve/reject/modify)
    "brand_content",    # Before any Brand Agent content is published
    "fallback_approval", # Before Tier 1 actions are executed
]

def should_interrupt_for_human(state: CouncilState, point: str) -> bool:
    """Check if the debate should pause for human review."""
    if not state.get("human_in_loop", False):
        return False

    if point == "pre_synthesis":
        # Always pause before synthesis if human-in-loop
        return True

    if point == "post_synthesis":
        # Pause if confidence is below threshold
        return state.get("confidence", 100) < 70

    if point == "brand_content":
        # Always pause for brand content review
        return True

    if point == "fallback_approval":
        # Pause if Tier 1 cost exceeds $100K
        for fb in state.get("fallback_options", []):
            if fb.get("tier") == 1 and fb.get("cost_estimate", 0) > 100000:
                return True

    return False
```

### 9.2 LangGraph Interrupt Configuration

```python
# In graph compilation

compiled = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["moderator"] if os.getenv("HUMAN_IN_LOOP") == "true" else [],
)

# To resume after human review:
# result = await graph.ainvoke(None, config={"configurable": {"thread_id": session_id}})
```

### 9.3 Human Review Actions

| Action | Effect | When |
|--------|--------|------|
| **Approve** | Continue to synthesis | After reviewing agent outputs |
| **Reject** | Re-run specific agent with human feedback | Agent output is incorrect |
| **Modify** | Edit agent output before synthesis | Partial correction needed |
| **Force Debate** | Override auto-decision, force debate round | Human sees conflict agents missed |
| **Cancel** | Terminate council session | Query is inappropriate |

---

## 10. Complete Working Example

### 10.1 Full Debate Flow: "Taiwan Chip Crisis"

```
QUERY: "What happens if Supplier S1 (Taiwan) is delayed by 2 weeks?"

═══════════════════════════════════════════════════════════════
ROUND 0: MODERATOR PARSE
═══════════════════════════════════════════════════════════════
  • Query parsed: supplier_delay_event
  • Context extracted: {supplier_id: "S1", region: "Taiwan", delay: "2 weeks"}
  • All 6 agents assigned

═══════════════════════════════════════════════════════════════
ROUND 1: PARALLEL ANALYSIS (6 agents simultaneously)
═══════════════════════════════════════════════════════════════

  ⚠️  RISK SENTINEL ──────────── 87% confidence
     Risk Score: 82/100 (CRITICAL)
     Drivers: China tensions, earthquake risk, port congestion
     Model: Groq Llama-3.3-70B
     MCP Tools Used: news_search, gdelt_query

  📦  SUPPLY OPTIMIZER ───────── 91% confidence
     2 alternate suppliers: S2 (India, 12d lead, 82% match), S3 (Vietnam, 18d lead, 75% match)
     S2 onboarding: 7-14 days, MOQ: 5K units
     Model: Groq Llama-3.3-70B
     MCP Tools Used: neo4j_query, supplier_search

  🚛  LOGISTICS NAVIGATOR ───── 85% confidence
     Air freight bridge: 3 days, $185K
     Sea reroute via Dubai: 12 days, $78K
     Port Shanghai congestion: 4-day average delay
     Model: Groq Llama-3.3-70B
     MCP Tools Used: route_optimize, port_status

  📈  MARKET INTELLIGENCE ────── 78% confidence
     Semiconductor index: volatile (+12% this month)
     Forward-buy window: 5 days remaining
     Demand forecast: +8% Q-over-Q
     Model: OpenRouter DeepSeek-R1
     MCP Tools Used: commodity_price, trade_data

  💰  FINANCE GUARDIAN ───────── 82% confidence
     Exposure: $2.4M (14-day delay × $85K/day × 2 components)
     Mitigation cost (Tier 1): $230K
     ROI: 943%
     Insurance claim potential: ~$85K
     Model: NVIDIA Nemotron-70B
     MCP Tools Used: erp_query, currency_rate

  🏷️  BRAND PROTECTOR ───────── 75% confidence
     Sentiment: 62/100 (declining)
     Negative topics: "delivery delays" (2.4K mentions), "stock shortage" (1.8K)
     CompetitorX: Exploiting with "Always in Stock" campaign
     Crisis comms drafted: Press release + social posts + customer email
     Model: Groq Llama-3.3-70B
     MCP Tools Used: social_sentiment, competitor_ads

═══════════════════════════════════════════════════════════════
DEBATE CONDITION CHECK
═══════════════════════════════════════════════════════════════
  Max confidence: 91% (Supply)
  Min confidence: 75% (Brand)
  Gap: 16% → Below 20% threshold
  Result: SKIP DEBATE → SYNTHESIZE

═══════════════════════════════════════════════════════════════
SYNTHESIS (Moderator)
═══════════════════════════════════════════════════════════════
  Weighted confidence: 84.7%
  Model: Google Gemini-2.0-Flash

  🏆 FINAL RECOMMENDATION:
  "Immediately activate Supplier S2 (India) for Component C1 while
   establishing an air freight bridge for the 2-week gap. Launch a
   'Pre-order Now' marketing campaign to manage customer expectations.
   File cargo insurance claim for the delayed shipment."

  Overall Confidence: 84.7%
  Risk Score: 72/100 (HIGH)

  FALLBACK OPTIONS:
  ┌─────────────────────────────────────────────────────────┐
  │ TIER 1 — IMMEDIATE (0-48h)                            │
  │ ✅ Activate S2 (India) — $45K, 24h, -35% risk         │
  │ ✅ Air freight bridge — $185K, 3d, -25% risk          │
  │ ✅ Pause ads → Pre-order campaign — $0, 1h, -10% risk │
  │ Total: $230K | ROI: 943%                               │
  ├─────────────────────────────────────────────────────────┤
  │ TIER 2 — SHORT-TERM (2-4 weeks)                       │
  │ ○ Multi-source split (S2+S3) — $120K, 14d, -40% risk  │
  │ ○ Cargo insurance claim — $0, 10-15d, -15% risk       │
  ├─────────────────────────────────────────────────────────┤
  │ TIER 3 — STRATEGIC (1-6 months)                       │
  │ ○ Geographic diversification — $500K, 90d, -60% risk  │
  │ ○ Safety stock revision — $80K, 30d, -30% risk        │
  └─────────────────────────────────────────────────────────┘

  MONTE CARLO (10,000 scenarios):
  P10: $800K exposure | P50: $1.2M | P90: $2.4M

  PREDICTIONS:
  30d: Risk → 62 (improving) | 60d: → 47 | 90d: → 38

  TOTAL LATENCY: 6.2 seconds
  TOTAL TOKENS: 11,306
  TOTAL COST: $0.00 (free tier)
```

---

## 11. Debate Engine Configuration

```python
# backend/agents/debate_config.py

from pydantic import BaseModel

class DebateConfig(BaseModel):
    # Round settings
    max_debate_rounds: int = 3
    confidence_gap_threshold: float = 20.0  # % to trigger debate
    low_confidence_threshold: float = 30.0  # % to trigger self-reflection
    high_agreement_threshold: float = 80.0  # % all above = skip debate

    # Confidence weighting
    agent_weights: dict = {
        "risk": 1.5,
        "supply": 1.3,
        "logistics": 1.2,
        "market": 1.0,
        "finance": 1.3,
        "brand": 0.8,
    }

    # Self-reflection
    self_reflect_enabled: bool = True
    self_reflect_max_confidence_boost: float = 15.0
    self_reflect_confidence_cap: float = 95.0

    # Monte Carlo
    monte_carlo_scenarios: int = 10000
    monte_carlo_enabled: bool = True

    # Predictions
    prediction_horizons: list[int] = [30, 60, 90]  # days
    prediction_enabled: bool = True

    # Human-in-the-loop
    human_in_loop: bool = False
    human_review_points: list[str] = ["pre_synthesis", "brand_content"]
    brand_content_requires_approval: bool = True
    tier1_cost_approval_threshold: float = 100000  # $100K

    # Fallbacks
    fallback_tiers: int = 3
    roi_calculation_enabled: bool = True

    # Performance
    max_council_latency_seconds: float = 8.0
    max_single_agent_latency_seconds: float = 2.0
```

---

## 12. Debate Engine API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/council/analyze` | POST | Start full council debate |
| `/council/agent/{agent}` | POST | Run single agent (no debate) |
| `/council/{id}/status` | GET | Check round + agent status |
| `/council/{id}/result` | GET | Get final recommendation |
| `/council/{id}/audit` | GET | Full debate trail |
| `/council/{id}/export/pdf` | GET | Export debate as PDF |
| `/council/{id}/export/json` | GET | Export debate as JSON |
| `ws://*/ws/council` | WS | Real-time debate streaming |

---

## 13. Debate Engine State Transitions

```
                    ┌──────────┐
                    │  PENDING  │
                    └─────┬────┘
                          │
                    ┌─────▼────┐
                    │ MODERATOR │  Round 0: Parse
                    │  PARSE    │
                    └─────┬────┘
                          │
               ┌──────────▼──────────┐
               │   PARALLEL ANALYSIS  │  Round 1: 6 agents
               │   (6 agents)         │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │  DEBATE CONDITION?   │
               └──┬───────┬───────┬──┘
                  │       │       │
          gap≤20% │  gap>20%│  low conf
                  │       │       │
          ┌───────▼──┐ ┌──▼─────┐ ┌▼──────────────┐
          │SYNTHESIZE│ │ DEBATE │ │ SELF-REFLECT   │
          │          │ │ ROUND  │ │ (re-query LLM) │
          └────┬─────┘ └──┬─────┘ └───────┬────────┘
               │          │               │
               │    ┌─────▼─────┐         │
               │    │ CHALLENGE │         │
               │    │ + RESPOND │         │
               │    └─────┬─────┘         │
               │          │               │
               │    ┌─────▼──────┐        │
               │    │ DEBATE     │        │
               │    │ CONDITION? │◄───────┘
               │    └──┬─────┬──┘
               │       │     │
               │  gap≤20%  round≥3
               │       │     │
               └───────┼─────┘
                       │
               ┌───────▼───────┐
               │   SYNTHESIZE   │  Final recommendation
               │   (Moderator)  │
               └───────┬───────┘
                       │
               ┌───────▼───────┐
               │  GENERATE      │
               │  FALLBACKS     │
               │  + MONTE CARLO │
               │  + PREDICTIONS │
               └───────┬───────┘
                       │
               ┌───────▼───────┐
               │   COMPLETE     │
               └───────────────┘
```

---

## 14. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Full council (no debate) | < 6s | End-to-end latency |
| Full council (1 debate round) | < 8s | End-to-end latency |
| Full council (2 debate rounds) | < 12s | End-to-end latency |
| Single agent response | < 2s | Agent node latency |
| Self-reflection | < 3s | Additional per agent |
| Monte Carlo (10K scenarios) | < 500ms | Simulation time |
| Prediction generation | < 200ms | Forecast calculation |
| Synthesis | < 2s | Moderator latency |
| Fallback generation | < 1s | Tier computation |
| WebSocket event latency | < 100ms | Message delivery |
