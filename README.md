# RailMind: Railway Passenger Intelligence & Decision Engine

> **Track 1 Prototype**  
> An intelligence and decision-support layer operating above railway information systems. Converts changing railway operational conditions into passenger-specific impact analysis, deterministic decisions, and clear natural-language explanations powered by the **AWS Strands Agents SDK**.

---

## 1. Core Architecture

The central pipeline is designed around a strictly deterministic decision core with AI exclusively serving as an explanation layer:

```
Railway Event
      │
      ▼
[Railway API Adapter] (backend/integrations/railway_api.py)
      │
      ▼ (Normalized Data)
[Event Intelligence Engine] (backend/engines/event_engine.py)
      │
      ▼ (State Recalculation)
[Journey State Engine] (backend/engines/journey_state.py)
      │
      ▼ (Buffer & Transfer Analysis)
[Impact Engine] (backend/engines/impact_engine.py)
      │
      ▼ (Deterministic Constraints)
[Decision Engine] (backend/engines/decision_engine.py)
      │
      ▼ (Structured 4-Point Recommendation)
[Action Engine] (backend/engines/action_engine.py)
   /             \
  /               \
 ▼                 ▼
[AWS Strands Agent]   [SQLite3 Database]
(backend/ai/          (railway.db: journeys, legs,
 strands_agent.py)     events, decisions, audit)
  \                 /
   ▼               ▼
[Passenger Operations Dashboard] (React + Vite + Tailwind)
```

---

## 2. Key Architectural Guarantees

1. **AI Never Makes Railway Decisions**: The `Decision Engine` uses rigorous deterministic mathematical formulas and threshold rules. AI does not hallucinate transfer buffers or make unauthorized rebooking promises.
2. **Strands Agent Explanation Layer**: Strands receives *only* the structured decision JSON from the Action Engine and synthesizes clear, empathetic explanations for the passenger. Works offline locally without requiring Amazon Bedrock credentials.
3. **Data Transparency**: The application visibly displays data source provenance as either `● LIVE DATA` or `● SIMULATED DATA`.
4. **Relational SQLite Persistence**: 10 relational tables maintain journeys, legs, bookings, trains, stations, events, decisions, and recommendations.

---

## 3. Technology Stack

- **Frontend**:
  - React 18
  - Vite 5
  - TypeScript
  - Tailwind CSS (Railway operations dark navy + white theme)
  - Lucide React Icons
  - Recharts / Custom Visualizers
- **Backend**:
  - Python 3.12
  - FastAPI
  - Pydantic v2
  - SQLAlchemy v2 + SQLite3 (`railway.db`)
  - Server-Sent Events (SSE) via `sse-starlette`
- **Agent SDK**:
  - **AWS Strands Agents SDK** (`strands-agents` v1.56)

---

## 4. Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+

### Running the Backend
From the project root:
```bash
# Option A: Using the Windows batch script
run_backend.bat

# Option B: Manual execution
$env:PYTHONPATH = "C:\Users\kisho\Documents\RailIntel"
backend\venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend will start at `http://127.0.0.1:8000`.

### Running the Frontend
In a separate terminal:
```bash
# Option A: Using the Windows batch script
run_frontend.bat

# Option B: Manual execution
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
Open `http://localhost:5173` in your browser.

---

## 5. End-to-End Demo Walkthrough

1. **Load Demo Journey**:
   - On the **My Journey** tab, click **Load Demo Journey**.
   - Inspect the itinerary: **Coimbatore (CBE)** ➔ **Chennai Central (MAS)** (Train 12601) connecting to **New Delhi (NDLS)** (Train 12615).
   - Baseline State: Arrival 08:30, Connection Departure 09:20. Initial transfer buffer is **50 minutes** (`SAFE` status).
2. **Trigger Disruption in Simulation Console**:
   - Navigate to the **Simulation Console** tab.
   - Click `[⚡ Inject +75m Delay]`.
   - Watch the animated 6-stage pipeline illuminate as the event travels through the backend engines.
3. **Inspect Real-time Passenger Impact**:
   - Return to **My Journey** (or watch it live-update via SSE):
     - Expected Arrival becomes **09:45**.
     - Remaining Transfer Buffer reduces from 50m to **10 minutes** (below the 30m safety threshold).
     - Impact Panel displays `CONNECTION AT RISK` (Severity: HIGH).
     - Decision Panel assessment: `Alternative connection should be reviewed while actively monitoring running speed.`
     - **Strands AI card** provides clear natural-language guidance:
       > *"Your train is currently 75 minutes behind schedule. This reduces your connection buffer to 10 minutes, below the configured 30-minute safety threshold. Your connection is therefore at risk. You can review another connection or continue monitoring the current journey."*
4. **Interactive Actions**:
   - Click `[Review Alternative Connections]` to inspect backup trains from Chennai Central (e.g. Train 12621 Tamil Nadu Express).
   - Click `[Continue Monitoring]` or `[Set Delay Alert]`.
5. **Inspect System Architecture & Flow**:
   - Open the **Architecture & Flow** tab to view the live component diagnostics, SQLite table stats, and the pipeline diagram.
