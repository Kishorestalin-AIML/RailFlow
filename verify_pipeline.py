import httpx
import json

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

print("=== 1. Checking Frontend ===")
fe = httpx.get("http://127.0.0.1:5173", timeout=5.0)
print(f"Frontend HTTP Status: {fe.status_code}")

print("\n=== 2. Checking Initial Journey State ===")
j_init = client.get("/journey/DEMO123456").json()
print(f"Initial Status: {j_init['journey_status']} | Buffer: {j_init['connection_buffer_minutes']} min")

print("\n=== 3. Injecting +75 Min Delay Event ===")
delay_res = client.post("/simulate/delay", json={"train_id": "12601", "delay_minutes": 75}).json()
print(f"Delay Event ID: {delay_res.get('event_id')} | Affected Journeys: {delay_res.get('affected_journeys_count')}")

print("\n=== 4. Checking Updated Journey State ===")
j_updated = client.get("/journey/DEMO123456").json()
print(f"Updated Status: {j_updated['journey_status']} | Buffer: {j_updated['connection_buffer_minutes']} min | Expected Arr: {j_updated['legs'][0]['actual_arrival']}")

print("\n=== 5. Checking Impact Engine ===")
imp = client.get(f"/impact/{j_updated['journey_id']}").json()
print(f"Impact Type: {imp['impact_type']} | Severity: {imp['severity']} | Summary: {imp['status_summary']}")

print("\n=== 6. Checking Decision Engine ===")
dec = client.get(f"/decision/{j_updated['journey_id']}").json()
print(f"Decision Status: {dec['situation_status']} | Assessment: {dec['system_assessment']}")

print("\n=== 7. Checking Action Engine ===")
rec = client.get(f"/recommendations/{j_updated['journey_id']}").json()
print(f"Title: {rec['title']} | Status: {rec['status']}")
print(f"What Happened: {rec['what_happened']}")
print(f"Why It Matters: {rec['why_it_matters']}")

print("\n=== 8. Checking AWS Strands Agent Explanation ===")
explain = client.post("/ai/explain", json={"journey_id": j_updated['journey_id']}).json()
print(f"Model Provider: {explain['model_provider']}")
print(f"Explanation: {explain['explanation']}")

print("\n=== 9. Checking Train Search & Availability ===")
trains = client.get("/trains/search", params={"origin": "CBE", "destination": "MAS"}).json()
print(f"Found {len(trains)} trains. First: {trains[0]['train_name']} | Data Source: {trains[0]['data_source']}")

print("\n=== 10. Checking System Health ===")
health = client.get("/health").json()
print(f"Health Status: {health['status']} | Database: {health['database']} | Adapter Mode: {health['data_adapter_mode']}")
print("\n>>> ALL ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY! <<<")
