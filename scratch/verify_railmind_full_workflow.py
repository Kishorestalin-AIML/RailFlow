"""
End-to-End Verification Script for RailMind — Real-Time Railway Journey Intelligence.
Validates the complete functional pipeline from RailRadar live monitoring to automated alternative discovery,
GPT4All trade-off analysis, and SMS/Email passenger notification.
"""

import sys
import httpx
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def run_verification():
    print("================================================================================")
    print("   RAILMIND — REAL-TIME RAILWAY JOURNEY INTELLIGENCE: FULL WORKFLOW AUDIT")
    print("================================================================================")

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Health & Architecture Status
    print("\n[Step 1] System Health & RailRadar Diagnostics:")
    health = client.get("/health").json()
    status = client.get("/system/status").json()
    print(f"  • Status: {health.get('status')} | Database: {health.get('database')}")
    print(f"  • RailRadar Base URL: {status['railradar_api']['base_url']}")
    print(f"  • RailRadar Provider Status: {status['railradar_api']['mode']}")
    print(f"  • Local LLM Engine: {status['gpt4all_llm']['model_name']} ({status['gpt4all_llm']['status']})")
    assert health.get("status") == "HEALTHY", "Health check failed"

    # 2. Passenger Onboarding (Section 17 & 19)
    print("\n[Step 2] Passenger Registration & Contact Setup:")
    passenger_payload = {
        "name": "Kishore Stalin",
        "email": "kishore@example.com",
        "phone": "+91 98401 23456",
        "email_notifications_enabled": True,
        "sms_notifications_enabled": True
    }
    p_res = client.post("/passengers", json=passenger_payload)
    assert p_res.status_code == 200, f"Registration failed: {p_res.text}"
    p_data = p_res.json()
    passenger_id = p_data["passenger_id"]
    print(f"  • Registered: {p_data['name']} (ID: {passenger_id})")
    print(f"  • Contact: Email: {p_data['email']} | Mobile: {p_data['phone']}")
    print(f"  • SMS Alerts: {p_data['sms_notifications_enabled']} | Email Alerts: {p_data['email_notifications_enabled']}")

    # 3. Active Journey Setup (Section 18)
    print("\n[Step 3] Active Journey Registration (Coimbatore ➔ New Delhi):")
    journey_payload = {
        "passenger_id": passenger_id,
        "from_station": "CBE",
        "to_station": "NDLS",
        "journey_date": "2026-09-20",
        "train_number": "12601"
    }
    j_res = client.post("/journey", json=journey_payload)
    assert j_res.status_code == 200, f"Journey creation failed: {j_res.text}"
    j_data = j_res.json()
    journey_id = j_data["journey_id"]
    print(f"  • Journey ID: {journey_id} | PNR: {j_data['pnr']}")
    print(f"  • Route: {j_data['source_station']['name']} ➔ {j_data['destination_station']['name']}")
    print(f"  • Monitored Train: {j_data['legs'][0]['train_number']} ({j_data['legs'][0]['train_name']})")
    print(f"  • Initial Running Status: {j_data['journey_status']} (Expected Arrival: {j_data['legs'][0]['scheduled_arrival']})")

    # 4. Ingest Disruption Event (Section 6 & 7: Real-Time Delay Detection)
    print("\n[Step 4] Real-Time RailRadar Delay Detection (+65 Minutes):")
    event_payload = {
        "event_type": "TRAIN_DELAY",
        "train_id": "12601",
        "delay_minutes": 65,
        "source": "RailRadar Live API"
    }
    e_res = client.post("/events", json=event_payload)
    assert e_res.status_code == 200, f"Event ingestion failed: {e_res.text}"
    e_data = e_res.json()
    print(f"  • Event Ingested: {e_data['event_type']} on Train {e_data['train_id']}")
    print(f"  • Delay Delta: +{e_data['delay_change']} min (Total Delay: {e_data['new_delay']} min)")
    print(f"  • Pipeline Steps Generated: {len(e_data['pipeline_steps'])}")

    # 5. Verify Journey Impact Recalculation (Section 8)
    print("\n[Step 5] Downstream Journey Impact Recalculation:")
    impact = client.get(f"/impact/{journey_id}").json()
    decision = client.get(f"/decision/{journey_id}").json()
    print(f"  • Severity: {impact['severity']} | Impact Type: {impact['impact_type']}")
    print(f"  • Delayed Train Expected Arrival: {impact['expected_arrival']}")
    print(f"  • Remaining Connection Buffer: {impact['remaining_buffer_minutes']} min (Required: {impact['required_buffer_minutes']} min)")
    print(f"  • Decision Assessment: {decision['system_assessment']}")
    print(f"  • Situation Status: {decision['situation_status']}")
    assert decision['situation_status'] in ["AT_RISK", "CRITICAL", "MISSED"], "Expected AT_RISK or MISSED state"

    # 6. Automatic Alternative Trains & Stations Engine (Section 9, 10, 11, 27)
    print("\n[Step 6] Automatic Alternative Discovery & Factual Comparison:")
    alts = client.get(f"/alternatives/{journey_id}").json()
    candidates = alts.get("alternatives", [])
    print(f"  • Total Candidates Evaluated: {alts.get('all_evaluated_count')}")
    print(f"  • Feasible Options Identified: {alts.get('feasible_count')}")
    print("\n  Comparison Table:")
    print(f"  {'Option':<7} | {'Train':<7} | {'Station':<18} | {'Dep':<6} | {'Dest Arrival':<13} | {'Transfer':<12} | {'Availability':<18} | {'Fare':<8}")
    print("  " + "-" * 100)

    # Current planned
    cur = alts.get("current_journey", {})
    print(f"  {'Current':<7} | {cur.get('train', ''):<7} | {cur.get('station', ''):<18} | {cur.get('departure', ''):<6} | {cur.get('expected_destination_arrival', ''):<13} | {'Direct':<12} | {cur.get('availability', ''):<18} | {cur.get('formatted_fare', ''):<8}")

    for a in candidates:
        opt = a.get("option_letter", "Alt")
        tr = a.get("train_number", "")
        st = a.get("station_name", "")[:18]
        dep = a.get("departure_time", "")
        dest_arr = a.get("expected_destination_arrival", "")
        tr_min = f"{a.get('transfer_time_minutes')} min" if a.get('transfer_time_minutes') else "Same stn"
        av = a.get("availability", "")[:18]
        fare = a.get("formatted_fare", "")
        print(f"  {opt:<7} | {tr:<7} | {st:<18} | {dep:<6} | {dest_arr:<13} | {tr_min:<12} | {av:<18} | {fare:<8}")

    assert len(candidates) >= 1, "At least 1 feasible alternative option should be discovered"

    # 7. Local GPT4All Assistant Explanation (Section 14, 15, 16, 28)
    print("\n[Step 7] Local GPT4All Natural Language Trade-Off Explanation:")
    exp = client.post("/ai/explain", json={"journey_id": journey_id}).json()
    print(f"  • Provider: {exp['model_provider']} ({exp['model_name']})")
    print("  • Structured Explanation:")
    for line in exp["explanation"].split("\n"):
        print(f"    {line}")

    assert "What changed?" in exp["explanation"]
    assert "Why does it matter?" in exp["explanation"]
    assert "Important trade-offs" in exp["explanation"]

    # 8. Notifications Audit (Section 20, 21, 22)
    print("\n[Step 8] Passenger Multi-Channel Notification Audit (SMS & Email):")
    notifs = client.get("/notifications").json()
    print(f"  • Total Dispatched Alerts Logged: {len(notifs)}")
    for n in notifs[:4]:
        print(f"    - [{n['channel']}] {n['notification_type']} -> Status: {n['status']} (ID: {n['notification_id']})")
        print(f"      Content: {n['message'][:90]}...")

    print("\n================================================================================")
    print("   ✓ ALL RAILMIND VERIFICATION AUDITS PASSED SUCCESSFULLY!")
    print("================================================================================")

if __name__ == "__main__":
    run_verification()
