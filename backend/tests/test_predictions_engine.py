"""Tests for PredictionsEngine: Monte Carlo, Prophet fallback, LSTM stub, ensemble."""

import pytest
import math
from backend.predictions_engine import (
    monte_carlo_disruption, prophet_forecast, lstm_forecast,
    ensemble_predict, _simple_trend_forecast, generate_predictions_for_debate,
)
from backend.state import Prediction


# ---------------------------------------------------------------------------
# Monte Carlo simulation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_monte_carlo_returns_prediction():
    result = await monte_carlo_disruption(base_probability=0.3, simulations=1000, horizon_days=90)
    assert isinstance(result, Prediction)
    assert result.metric == "disruption_probability"
    assert result.method == "monte_carlo"
    assert 0 <= result.point_estimate <= 1.0
    assert result.ci_lower <= result.point_estimate <= result.ci_upper
    assert result.data_points_used == 1000


@pytest.mark.asyncio
async def test_monte_carlo_high_base_probability():
    result = await monte_carlo_disruption(base_probability=0.8, simulations=1000, horizon_days=30)
    assert result.point_estimate > 0.5


@pytest.mark.asyncio
async def test_monte_carlo_with_historical_data():
    disruptions = [{"type": "historical", "context": "earthquake 2023"}]
    result = await monte_carlo_disruption(
        base_probability=0.3, simulations=1000, horizon_days=90,
        historical_disruptions=disruptions,
    )
    # Should have higher probability with historical data
    assert result.point_estimate > 0


@pytest.mark.asyncio
async def test_monte_carlo_ci_width():
    result = await monte_carlo_disruption(base_probability=0.3, simulations=5000, horizon_days=90)
    ci_width = result.ci_upper - result.ci_lower
    assert ci_width > 0  # CI should have non-zero width
    assert ci_width < 1.0  # But not absurdly wide


# ---------------------------------------------------------------------------
# Simple trend forecast
# ---------------------------------------------------------------------------
def test_simple_trend_with_data():
    data = [{"ds": "2025-01-01", "y": 100}, {"ds": "2025-02-01", "y": 110},
            {"ds": "2025-03-01", "y": 120}]
    result = _simple_trend_forecast(data, "price", 90)
    assert isinstance(result, Prediction)
    assert result.method == "simple_trend"
    assert result.point_estimate > 100  # trending up
    assert result.ci_lower < result.point_estimate < result.ci_upper


def test_simple_trend_empty_data():
    result = _simple_trend_forecast([], "price", 90)
    assert result.point_estimate == 0.0
    assert result.confidence == 0.1


def test_simple_trend_single_point():
    data = [{"ds": "2025-01-01", "y": 50}]
    result = _simple_trend_forecast(data, "price", 30)
    assert result.point_estimate == 50.0  # no trend with single point


def test_simple_trend_no_y_key():
    data = [{"ds": "2025-01-01", "x": 100}]
    result = _simple_trend_forecast(data, "price", 30)
    assert result.point_estimate == 0.0


# ---------------------------------------------------------------------------
# Prophet forecast (falls back to simple_trend if prophet not installed)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prophet_forecast_fallback():
    data = [{"ds": "2025-01-01", "y": 100}, {"ds": "2025-02-01", "y": 110},
            {"ds": "2025-03-01", "y": 120}]
    result = await prophet_forecast(data, "price", 90)
    assert isinstance(result, Prediction)
    assert result.metric == "price"
    # Method is either "prophet" or "simple_trend" depending on availability
    assert result.method in ("prophet", "simple_trend")


@pytest.mark.asyncio
async def test_prophet_forecast_insufficient_data():
    result = await prophet_forecast([{"ds": "2025-01-01", "y": 100}], "price", 90)
    assert result.method == "simple_trend"


# ---------------------------------------------------------------------------
# LSTM stub
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_lstm_forecast():
    data = [{"ds": "2025-01-01", "y": 100}, {"ds": "2025-02-01", "y": 110}]
    result = await lstm_forecast(data, "price", 90)
    assert result.method == "lstm_stub"
    assert result.confidence <= 0.5  # stub has reduced confidence


# ---------------------------------------------------------------------------
# Ensemble predict
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensemble_predict_price():
    data = [{"ds": "2025-01-01", "y": 100}, {"ds": "2025-02-01", "y": 110},
            {"ds": "2025-03-01", "y": 120}]
    results = await ensemble_predict("chip shortage", "price", 90, data, "market")
    assert len(results) >= 2  # at least prophet + lstm
    methods = [r.method for r in results]
    assert "ensemble" in methods


@pytest.mark.asyncio
async def test_ensemble_predict_disruption():
    results = await ensemble_predict("chip shortage", "disruption_probability", 90, [], "finance")
    methods = [r.method for r in results]
    assert "monte_carlo" in methods


@pytest.mark.asyncio
async def test_ensemble_predict_ci_valid():
    data = [{"ds": "2025-01-01", "y": 100}, {"ds": "2025-02-01", "y": 110}]
    results = await ensemble_predict("test", "price", 90, data, "market")
    for r in results:
        assert r.ci_lower <= r.point_estimate <= r.ci_upper, f"CI invalid for {r.method}"


# ---------------------------------------------------------------------------
# generate_predictions_for_debate
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_predictions_for_debate():
    state = {"query": "Taiwan chip crisis", "context": {}}
    results = await generate_predictions_for_debate("Taiwan chip crisis", state)
    assert isinstance(results, list)
    # Should have predictions from market, finance, supply
    metrics = [p["metric"] for p in results]
    assert "price" in metrics or "disruption_probability" in metrics
