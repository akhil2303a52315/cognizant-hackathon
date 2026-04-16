"""Predictions Engine for SupplyChainGPT Council.

Ensemble predictions using:
  - Prophet (Facebook/Meta time-series forecasting) — when available
  - Simple LSTM stub (placeholder for production LSTM)
  - Monte Carlo simulation for disruption probability
  - LLM-augmented forecasting using RAG historical data

Used by Market Agent & Finance Agent for price/disruption forecasts.
Returns predictions with confidence intervals.
"""

import math
import random
import logging
import time as _time
from typing import Optional
from datetime import datetime, timezone

from backend.state import Prediction
from backend.observability.langsmith_config import CouncilTracer, record_agent_call

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Monte Carlo Simulation
# ---------------------------------------------------------------------------
async def monte_carlo_disruption(
    base_probability: float = 0.3,
    volatility: float = 0.15,
    simulations: int = 10000,
    horizon_days: int = 90,
    historical_disruptions: list[dict] = None,
) -> Prediction:
    """Monte Carlo simulation for supply chain disruption probability.

    Simulates `simulations` paths over `horizon_days` using geometric
    Brownian motion with jump-diffusion for disruption events.

    Args:
        base_probability: Base disruption probability (0-1)
        volatility: Volatility of disruption probability
        simulations: Number of Monte Carlo paths
        horizon_days: Forecast horizon in days
        historical_disruptions: RAG-retrieved historical disruption data

    Returns:
        Prediction with point estimate and 95% CI
    """
    import asyncio

    if historical_disruptions:
        n_events = len(historical_disruptions)
        base_probability = min(base_probability + 0.02 * n_events, 0.95)

    def _run_simulation() -> list[float]:
        results = []
        dt = 1.0 / 252
        for _ in range(simulations):
            prob = base_probability
            for day in range(horizon_days):
                drift = 0.0
                diffusion = volatility * math.sqrt(dt) * random.gauss(0, 1)
                jump = 0.0
                if random.random() < 0.01:
                    jump = random.gauss(0, 0.1)
                prob = prob * math.exp(drift + diffusion + jump)
                prob = max(0.0, min(1.0, prob))
            results.append(prob)
        results.sort()
        return results

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _run_simulation)
    n = len(results)
    point = results[n // 2]
    ci_lower = results[int(n * 0.025)]
    ci_upper = results[int(n * 0.975)]

    return Prediction(
        metric="disruption_probability",
        horizon_days=horizon_days,
        point_estimate=round(point, 4),
        ci_lower=round(ci_lower, 4),
        ci_upper=round(ci_upper, 4),
        confidence=round(1.0 - (ci_upper - ci_lower), 3),
        method="monte_carlo",
        data_points_used=simulations,
    )


# ---------------------------------------------------------------------------
# Prophet Forecasting (with graceful fallback)
# ---------------------------------------------------------------------------
async def prophet_forecast(
    historical_data: list[dict],
    metric: str = "price",
    horizon_days: int = 90,
) -> Prediction:
    """Prophet time-series forecasting for price/demand trends.

    Attempts to use Prophet library; falls back to simple exponential
    smoothing if Prophet is unavailable.

    Args:
        historical_data: List of {"ds": "YYYY-MM-DD", "y": float} points
        metric: Metric name for the prediction
        horizon_days: Forecast horizon in days

    Returns:
        Prediction with point estimate and 95% CI
    """
    if not historical_data or len(historical_data) < 3:
        return _simple_trend_forecast(historical_data, metric, horizon_days)

    try:
        from prophet import Prophet as ProphetModel
        import pandas as pd

        df = pd.DataFrame(historical_data)
        if "ds" not in df.columns or "y" not in df.columns:
            return _simple_trend_forecast(historical_data, metric, horizon_days)

        model = ProphetModel(interval_width=0.95, yearly_seasonality=True)
        model.fit(df)

        future = model.make_future_dataframe(periods=horizon_days)
        forecast = model.predict(future)

        last_row = forecast.iloc[-1]
        point = float(last_row["yhat"])
        ci_lower = float(last_row["yhat_lower"])
        ci_upper = float(last_row["yhat_upper"])

        return Prediction(
            metric=metric,
            horizon_days=horizon_days,
            point_estimate=round(point, 4),
            ci_lower=round(ci_lower, 4),
            ci_upper=round(ci_upper, 4),
            confidence=0.7,
            method="prophet",
            data_points_used=len(historical_data),
        )

    except ImportError:
        logger.info("Prophet not available — using simple trend forecast")
        return _simple_trend_forecast(historical_data, metric, horizon_days)
    except Exception as e:
        logger.warning(f"Prophet forecast failed: {e} — falling back to simple trend")
        return _simple_trend_forecast(historical_data, metric, horizon_days)


def _simple_trend_forecast(
    historical_data: list[dict],
    metric: str,
    horizon_days: int,
) -> Prediction:
    """Simple exponential smoothing fallback when Prophet is unavailable.

    Uses weighted average of recent data points with linear trend extrapolation.
    """
    if not historical_data:
        return Prediction(
            metric=metric,
            horizon_days=horizon_days,
            point_estimate=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            confidence=0.1,
            method="simple_trend",
            data_points_used=0,
        )

    values = [d.get("y", 0) for d in historical_data if "y" in d]
    if not values:
        return Prediction(
            metric=metric,
            horizon_days=horizon_days,
            point_estimate=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            confidence=0.1,
            method="simple_trend",
            data_points_used=0,
        )

    # Weighted moving average (more weight to recent)
    n = len(values)
    weights = list(range(1, n + 1))
    weighted_avg = sum(v * w for v, w in zip(values, weights)) / sum(weights)

    # Linear trend
    if n >= 2:
        trend = (values[-1] - values[0]) / n
    else:
        trend = 0

    point = weighted_avg + trend * horizon_days

    # Confidence interval based on volatility
    volatility = math.sqrt(sum((v - weighted_avg) ** 2 for v in values) / n) if n > 1 else abs(point) * 0.2
    ci_width = 1.96 * volatility * math.sqrt(horizon_days / 30)

    return Prediction(
        metric=metric,
        horizon_days=horizon_days,
        point_estimate=round(point, 4),
        ci_lower=round(point - ci_width, 4),
        ci_upper=round(point + ci_width, 4),
        confidence=round(max(0.1, 0.5 - volatility / max(abs(point), 1)), 3),
        method="simple_trend",
        data_points_used=n,
    )


# ---------------------------------------------------------------------------
# LSTM Stub (placeholder for production LSTM)
# ---------------------------------------------------------------------------
async def lstm_forecast(
    historical_data: list[dict],
    metric: str = "price",
    horizon_days: int = 90,
) -> Prediction:
    """LSTM forecast stub — returns simple trend with LSTM label.

    In production, this would use a trained PyTorch/TensorFlow LSTM model.
    Currently falls back to simple_trend_forecast with LSTM method tag.
    """
    result = _simple_trend_forecast(historical_data, metric, horizon_days)
    # Override method label
    return Prediction(
        metric=result.metric,
        horizon_days=result.horizon_days,
        point_estimate=result.point_estimate,
        ci_lower=result.ci_lower,
        ci_upper=result.ci_upper,
        confidence=round(result.confidence * 0.8, 3),  # slightly lower confidence for stub
        method="lstm_stub",
        data_points_used=result.data_points_used,
    )


# ---------------------------------------------------------------------------
# Ensemble Prediction
# ---------------------------------------------------------------------------
async def ensemble_predict(
    query: str,
    metric: str = "price",
    horizon_days: int = 90,
    historical_data: list[dict] = None,
    agent_name: str = "market",
) -> list[Prediction]:
    """Run ensemble predictions using multiple methods.

    Combines Prophet, LSTM stub, and Monte Carlo into a weighted ensemble.
    Also uses RAG data for historical disruption context.

    Args:
        query: The original query (for RAG context)
        metric: What to predict ("price", "disruption_probability", "lead_time")
        horizon_days: Forecast horizon
        historical_data: Historical data points for forecasting
        agent_name: Agent requesting the prediction

    Returns:
        List of Prediction objects (individual methods + ensemble)
    """
    historical_data = historical_data or []
    predictions = []
    tracer = CouncilTracer(f"predictions_{agent_name}")

    # 1. Prophet forecast
    t0 = _time.monotonic()
    try:
        with tracer.trace_agent(agent_name, round_number=0, method="prophet"):
            prophet_pred = await prophet_forecast(historical_data, metric, horizon_days)
        predictions.append(prophet_pred)
    except Exception as e:
        logger.warning(f"Prophet forecast failed: {e}")
    latency_prophet = (_time.monotonic() - t0) * 1000
    record_agent_call(agent_name, f"predictions_{agent_name}", "prophet", latency_ms=latency_prophet)

    # 2. LSTM stub
    t0 = _time.monotonic()
    try:
        with tracer.trace_agent(agent_name, round_number=0, method="lstm_stub"):
            lstm_pred = await lstm_forecast(historical_data, metric, horizon_days)
        predictions.append(lstm_pred)
    except Exception as e:
        logger.warning(f"LSTM forecast failed: {e}")
    latency_lstm = (_time.monotonic() - t0) * 1000
    record_agent_call(agent_name, f"predictions_{agent_name}", "lstm_stub", latency_ms=latency_lstm)

    # 3. Monte Carlo disruption probability
    if metric in ("disruption_probability", "risk", "lead_time"):
        t0 = _time.monotonic()
        try:
            with tracer.trace_agent(agent_name, round_number=0, method="monte_carlo"):
                rag_disruptions = await _get_rag_disruptions(query, agent_name)
                mc_pred = await monte_carlo_disruption(
                    base_probability=0.3,
                    horizon_days=horizon_days,
                    historical_disruptions=rag_disruptions,
                )
            predictions.append(mc_pred)
        except Exception as e:
            logger.warning(f"Monte Carlo simulation failed: {e}")
        latency_mc = (_time.monotonic() - t0) * 1000
        record_agent_call(agent_name, f"predictions_{agent_name}", "monte_carlo", latency_ms=latency_mc)

    # 4. Ensemble (weighted average)
    if len(predictions) >= 2:
        weights = {"prophet": 0.4, "lstm_stub": 0.25, "monte_carlo": 0.35, "simple_trend": 0.2}
        total_weight = sum(weights.get(p.method, 0.1) for p in predictions)

        ensemble_point = sum(
            p.point_estimate * weights.get(p.method, 0.1) for p in predictions
        ) / total_weight

        ensemble_ci_lower = sum(
            p.ci_lower * weights.get(p.method, 0.1) for p in predictions
        ) / total_weight

        ensemble_ci_upper = sum(
            p.ci_upper * weights.get(p.method, 0.1) for p in predictions
        ) / total_weight

        ensemble_conf = sum(
            p.confidence * weights.get(p.method, 0.1) for p in predictions
        ) / total_weight

        predictions.append(Prediction(
            metric=metric,
            horizon_days=horizon_days,
            point_estimate=round(ensemble_point, 4),
            ci_lower=round(ensemble_ci_lower, 4),
            ci_upper=round(ensemble_ci_upper, 4),
            confidence=round(ensemble_conf, 3),
            method="ensemble",
            data_points_used=sum(p.data_points_used for p in predictions),
        ))

    return predictions


async def _get_rag_disruptions(query: str, agent_name: str) -> list[dict]:
    """Fetch historical disruption data from RAG for Monte Carlo calibration."""
    try:
        from backend.rag.agent_rag_integration import get_rag_context
        rag_ctx = await get_rag_context(agent_name, query)
        # Parse disruption events from RAG context
        disruptions = []
        if rag_ctx and "disruption" in rag_ctx.lower():
            # Simple heuristic: count disruption mentions
            disruptions.append({"type": "historical", "context": rag_ctx[:200]})
        return disruptions
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Convenience: generate predictions for the debate
# ---------------------------------------------------------------------------
async def generate_predictions_for_debate(query: str, state: dict) -> list[dict]:
    """Generate all predictions needed for the debate engine.

    Called by the graph's prediction node after agent fan-out.
    """
    context = state.get("context") or {}
    all_predictions = []

    # Market predictions (price forecast)
    try:
        market_preds = await ensemble_predict(
            query=query, metric="price", horizon_days=90, agent_name="market",
        )
        all_predictions.extend([p.model_dump() for p in market_preds])
    except Exception as e:
        logger.warning(f"Market predictions failed: {e}")

    # Finance predictions (disruption probability)
    try:
        finance_preds = await ensemble_predict(
            query=query, metric="disruption_probability", horizon_days=90, agent_name="finance",
        )
        all_predictions.extend([p.model_dump() for p in finance_preds])
    except Exception as e:
        logger.warning(f"Finance predictions failed: {e}")

    # Supply predictions (lead time)
    try:
        supply_preds = await ensemble_predict(
            query=query, metric="lead_time", horizon_days=60, agent_name="supply",
        )
        all_predictions.extend([p.model_dump() for p in supply_preds])
    except Exception as e:
        logger.warning(f"Supply predictions failed: {e}")

    return all_predictions
