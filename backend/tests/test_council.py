import httpx
import json

r = httpx.post(
    "http://localhost:8000/council/analyze",
    json={"query": "Taiwan semiconductor factory fire - what is the supply chain impact?"},
    headers={"X-API-Key": "dev-key"},
    timeout=120,
)

print(f"Status: {r.status_code}")
data = r.json()

for a in data.get("agent_outputs", []):
    print(f"\n--- {a['agent'].upper()} Agent ({a['model_used']}) ---")
    print(a["contribution"][:300])

print(f"\n--- SYNTHESIS ---")
print(data.get("recommendation", "None")[:500])
print(f"\nLatency: {data.get('latency_ms')}ms | Confidence: {data.get('confidence')}%")
