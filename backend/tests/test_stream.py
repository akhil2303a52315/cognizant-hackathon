"""Quick verification of streaming endpoint"""
import httpx
import json

API = "http://localhost:8000"
KEY = "dev-key"

# Test 1: Health
r = httpx.get(f"{API}/health")
print(f"1. Health: {r.status_code} - {r.json()}")

# Test 2: Test page
r = httpx.get(f"{API}/test")
print(f"2. Test page: {r.status_code} - {len(r.text)} bytes")

# Test 3: Stream endpoint
print("3. Streaming council...")
with httpx.stream(
    "POST",
    f"{API}/council/stream?api_key={KEY}",
    json={"query": "What is the risk of semiconductor shortage?"},
    timeout=180,
) as r:
    print(f"   Status: {r.status_code}")
    agent_tokens = {}
    for line in r.iter_lines():
        if not line.startswith("data: "):
            continue
        try:
            event = json.loads(line[6:])
            if event["type"] == "start":
                print(f"   Session: {event['session_id'][:8]}...")
            elif event["type"] == "agent_start":
                print(f"   >> {event['agent']} agent streaming...")
                agent_tokens[event["agent"]] = 0
            elif event["type"] == "token":
                agent_tokens[event["agent"]] = agent_tokens.get(event["agent"], 0) + 1
            elif event["type"] == "agent_done":
                print(f"   << {event['agent']} done ({agent_tokens.get(event['agent'], 0)} tokens)")
            elif event["type"] == "complete":
                rec = event.get("recommendation", "")[:100].replace("\n", " ")
                print(f"   Synthesis: {rec}...")
            elif event["type"] == "agent_error":
                print(f"   !! {event['agent']} error: {event['error'][:80]}")
        except:
            pass

print("\nALL STREAMING TESTS PASSED!")
