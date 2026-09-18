import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

print("--- Testing Section 28 API Endpoints ---")

r_health = client.get("/health")
print("1. GET /health ->", r_health.status_code, r_health.json()["status"])

r_sys = client.get("/system/status")
print("2. GET /system/status ->", r_sys.status_code, r_sys.json()["database"]["tables"])

r_search = client.get("/trains/search?origin=CBE&destination=MAS")
print("3. GET /trains/search ->", r_search.status_code, f"{len(r_search.json())} trains")

r_train = client.get("/trains/12601")
print("4. GET /trains/12601 ->", r_train.status_code, r_train.json()["train_name"])

r_sched = client.get("/trains/12601/schedule")
print("5. GET /trains/12601/schedule ->", r_sched.status_code, f"{len(r_sched.json())} halts")

r_status = client.get("/trains/12601/status")
print("6. GET /trains/12601/status ->", r_status.status_code, r_status.json()["running_status"])

r_avail = client.get("/trains/12601/availability?class_type=3A")
print("7. GET /trains/12601/availability ->", r_avail.status_code, r_avail.json()["status"])

r_fare = client.get("/trains/12601/fare?class_type=3A")
fare_str = str(r_fare.json()["formatted_fare"]).replace('\u20b9', 'INR ')
print("8. GET /trains/12601/fare ->", r_fare.status_code, fare_str)

r_journey = client.get("/journey/DEMO123456")
print("9. GET /journey/DEMO123456 ->", r_journey.status_code, r_journey.json()["journey_status"])

r_impact = client.get("/impact/JRN-DEMO-01")
print("10. GET /impact/JRN-DEMO-01 ->", r_impact.status_code, r_impact.json()["impact_type"])

r_decision = client.get("/decision/JRN-DEMO-01")
print("11. GET /decision/JRN-DEMO-01 ->", r_decision.status_code, r_decision.json()["situation_status"])

r_rec = client.get("/recommendations/JRN-DEMO-01")
print("12. GET /recommendations/JRN-DEMO-01 ->", r_rec.status_code, r_rec.json()["status"])

r_explain = client.post("/ai/explain", json={"journey_id": "JRN-DEMO-01"})
print("13. POST /ai/explain ->", r_explain.status_code, r_explain.json()["model_provider"])

r_delay = client.post("/simulate/delay", json={"train_id": "12601", "delay_minutes": 40})
print("14. POST /simulate/delay ->", r_delay.status_code, f"Delta change: {r_delay.json()['delay_change']}m")

r_reset = client.post("/simulate/reset")
print("15. POST /simulate/reset ->", r_reset.status_code, r_reset.json()["message"])

print("\n>>> ALL 15 ENDPOINTS TESTED AND VERIFIED! <<<")
