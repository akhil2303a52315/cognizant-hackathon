import random
import math
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def run_simulation(
    variables: list[dict],
    num_simulations: int = 1000,
    target_metric: str = "total_cost",
) -> dict:
    results = []
    for _ in range(num_simulations):
        sim_values = {}
        for var in variables:
            name = var["name"]
            dist = var.get("distribution", "normal")
            if dist == "normal":
                mean = var.get("mean", 0)
                std = var.get("std", 1)
                sim_values[name] = random.gauss(mean, std)
            elif dist == "uniform":
                low = var.get("low", 0)
                high = var.get("high", 1)
                sim_values[name] = random.uniform(low, high)
            elif dist == "triangular":
                low = var.get("low", 0)
                mode = var.get("mode", 0.5)
                high = var.get("high", 1)
                sim_values[name] = random.triangular(low, mode, high)
            else:
                sim_values[name] = var.get("mean", 0)

        if target_metric == "total_cost":
            result = sum(v for v in sim_values.values())
        elif target_metric == "risk_score":
            result = sum(v * w for v, w in zip(sim_values.values(), [0.3, 0.3, 0.2, 0.2]))
        else:
            result = sum(sim_values.values())

        results.append(result)

    results.sort()
    n = len(results)
    p10 = results[int(n * 0.10)]
    p50 = results[int(n * 0.50)]
    p90 = results[int(n * 0.90)]

    mean = sum(results) / n
    variance = sum((x - mean) ** 2 for x in results) / n
    std_dev = math.sqrt(variance)

    buckets = 20
    hist_min = results[0]
    hist_max = results[-1]
    bucket_width = (hist_max - hist_min) / buckets if hist_max != hist_min else 1
    histogram = [0] * buckets
    for r in results:
        idx = min(int((r - hist_min) / bucket_width), buckets - 1)
        histogram[idx] += 1

    return {
        "num_simulations": num_simulations,
        "target_metric": target_metric,
        "percentiles": {"p10": round(p10, 2), "p50": round(p50, 2), "p90": round(p90, 2)},
        "statistics": {"mean": round(mean, 2), "std_dev": round(std_dev, 2), "min": round(results[0], 2), "max": round(results[-1], 2)},
        "histogram": {"buckets": buckets, "counts": histogram, "range": [round(hist_min, 2), round(hist_max, 2)]},
        "confidence_90": [round(p10, 2), round(p90, 2)],
    }
