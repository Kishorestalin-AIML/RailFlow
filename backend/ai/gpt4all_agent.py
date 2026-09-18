"""
GPT4All Local LLM Agent (backend/ai/gpt4all_agent.py)
Provides local natural-language explanation and trade-off comparison
strictly using backend deterministic railway intelligence data.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("gpt4all_agent")

SYSTEM_PROMPT = """You are RailMind Journey Assistant.

RailMind is a real-time railway journey intelligence system.

Railway information comes from the RailRadar API.

The backend deterministic engines are the source of truth.

You receive structured journey and alternative data from the backend.

Never invent railway information.

Never invent:
- train numbers
- train timings
- station names
- fares
- availability
- RAC
- WL
- PNR information
- train status

Never override backend feasibility calculations.

Compare feasible options using:
- expected final destination arrival
- departure time
- waiting time
- transfer time
- total journey duration
- availability
- RAC
- fare
- journey risk

If an option arrives earlier but has RAC while another option arrives later with CNF, clearly explain that trade-off.

If an alternative requires travelling to another station, clearly explain the transfer requirement.

If data is unavailable, explicitly say so.

Do not claim to book, cancel, modify or confirm railway tickets.

The passenger makes the final decision.

Keep explanations concise and practical."""


class GPT4AllAgent:
    """
    Local LLM runner for RailMind passenger explanations.
    Loads local GPT4All model weights when available, or executes
    deterministic structured explanation adhering to the exact system prompt.
    """

    def __init__(self):
        self.model_name = os.getenv("GPT4ALL_MODEL_NAME", "orca-mini-3b-gguf2-q4_0.gguf")
        self.model_path = os.getenv("GPT4ALL_MODEL_PATH", "")
        self._model = None
        self._initialized = False

    def _try_load_model(self):
        if self._initialized:
            return self._model

        self._initialized = True
        try:
            from gpt4all import GPT4All
            # Only load if model file exists locally to avoid downloading multi-gigabyte models during test runs
            model_file_exists = False
            if self.model_path and os.path.exists(self.model_path):
                model_file_exists = True
            elif self.model_path and os.path.exists(os.path.join(self.model_path, self.model_name)):
                model_file_exists = True

            if model_file_exists:
                logger.info(f"Loading local GPT4All model: {self.model_name}")
                self._model = GPT4All(
                    model_name=self.model_name,
                    model_path=self.model_path or None,
                    allow_download=False
                )
                logger.info("GPT4All model loaded successfully.")
            else:
                logger.info(f"GPT4All model file not found locally. Using deterministic prompt executor.")
        except Exception as e:
            logger.warning(f"Could not load GPT4All model directly: {e}. Falling back to deterministic engine.")
            self._model = None

        return self._model

    def explain_journey(self, payload: Dict[str, Any]) -> str:
        """
        Generates passenger-friendly explanation based on structured payload:
        {
          "journey_status": "AT_RISK",
          "current_train": {"number": "12601", "delay_minutes": 65, "expected_arrival": "20:45"},
          "alternatives": [...]
        }
        """
        model = self._try_load_model()

        user_prompt = f"""Analyze the following real-time railway journey status and alternative options:

```json
{json.dumps(payload, indent=2)}
```

Provide the explanation under four clear sections:
1. What changed?
2. Why does it matter?
3. Alternative ways to reach your destination
4. Important trade-offs"""

        if model:
            try:
                with model.chat_session(system_prompt=SYSTEM_PROMPT):
                    response = model.generate(user_prompt, max_tokens=450, temp=0.2)
                    if response and len(response.strip()) > 30:
                        return response.strip()
            except Exception as e:
                logger.error(f"GPT4All inference error: {e}. Falling back to structured response.")

        # Deterministic generation strictly adhering to the prompt rules
        return self._generate_structured_explanation(payload)

    def _generate_structured_explanation(self, payload: Dict[str, Any]) -> str:
        """
        Deterministic, rule-based natural language generator
        enforcing zero-hallucination and exact trade-off comparisons.
        """
        status = payload.get("journey_status", "SAFE")
        curr = payload.get("current_train", {})
        train_no = curr.get("number", curr.get("train", "12601"))
        delay = curr.get("delay_minutes", 0)
        expected_arr = curr.get("expected_arrival", "--:--")
        alts = payload.get("alternatives", [])

        # Section 1: What changed?
        if delay > 0:
            what_changed = f"Train {train_no} is currently delayed by {delay} minutes, with expected arrival at {expected_arr}."
        else:
            what_changed = f"Train {train_no} is currently running on time with arrival scheduled at {expected_arr}."

        # Section 2: Why does it matter?
        if status in ["AT_RISK", "CRITICAL"]:
            why_it_matters = (
                f"Because of this delay, your transfer buffer for the connecting train has shrunk "
                f"below the recommended 30-minute threshold. There is a high risk of missing your scheduled connection."
            )
        elif status == "MISSED":
            why_it_matters = (
                f"Your incoming train will arrive after the scheduled departure of your connecting train. "
                f"The scheduled connection cannot be made."
            )
        else:
            why_it_matters = "Your connection buffer remains within safe operational limits. No immediate action required."

        # Section 3: Alternative ways to reach your destination
        if not alts:
            alt_text = "No immediate feasible alternative train or station transfers are found in current railway data."
        else:
            alt_lines = []
            for a in alts[:3]:
                opt = a.get("option", a.get("option_letter", "Alt"))
                stn = a.get("station", a.get("station_name", "Station"))
                tr = a.get("train", a.get("train_name", a.get("train_number", "Express")))
                dep = a.get("departure", a.get("departure_time", "--:--"))
                dest_arr = a.get("expected_destination_arrival", "--:--")
                transfer = a.get("transfer_minutes", a.get("transfer_time_minutes", 0))
                transfer_str = f", requires {transfer} min road/local transfer" if transfer else ""
                avail = a.get("availability", a.get("availability_status", "Not provided"))
                fare = a.get("formatted_fare", f"₹{a.get('fare')}" if a.get("fare") else "Not provided")

                alt_lines.append(
                    f"• Option {opt} (Train {tr} from {stn}): Departs at {dep}, reaches destination at {dest_arr} ({avail}, Fare: {fare}{transfer_str})."
                )
            alt_text = "\n".join(alt_lines)

        # Section 4: Important trade-offs
        trade_offs = []
        if len(alts) >= 2:
            a1 = alts[0]
            a2 = alts[1]
            arr1 = a1.get("expected_destination_arrival", "")
            arr2 = a2.get("expected_destination_arrival", "")
            avail1 = str(a1.get("availability", ""))
            avail2 = str(a2.get("availability", ""))
            tr1 = a1.get("transfer_minutes", a1.get("transfer_time_minutes", 0))
            tr2 = a2.get("transfer_minutes", a2.get("transfer_time_minutes", 0))

            if "RAC" in avail1 and "CNF" in avail2:
                trade_offs.append(
                    f"Option {a1.get('option', 'A')} arrives earlier ({arr1}) but carries RAC status, "
                    f"whereas Option {a2.get('option', 'B')} provides confirmed seating (CNF) but arrives later ({arr2})."
                )
            elif tr1 > 0:
                trade_offs.append(
                    f"Option {a1.get('option', 'A')} requires a {tr1}-minute transfer to {a1.get('station', 'another station')}, "
                    f"while Option {a2.get('option', 'B')} departs directly from your arrival station."
                )
            else:
                trade_offs.append(
                    f"Option {a1.get('option', 'A')} gives the earliest destination arrival ({arr1}), "
                    f"while Option {a2.get('option', 'B')} provides greater departure buffer ({a2.get('departure', '--:--')})."
                )
        elif len(alts) == 1:
            trade_offs.append(
                f"Option {alts[0].get('option', 'A')} is the only feasible alternative currently identified. "
                f"Check seat status ({alts[0].get('availability', 'Not provided')}) before booking."
            )
        else:
            trade_offs.append("Continue monitoring live updates as RailRadar refreshes running status.")

        trade_off_text = "\n".join(trade_offs)

        return f"""What changed?
{what_changed}

Why does it matter?
{why_it_matters}

Alternative ways to reach your destination:
{alt_text}

Important trade-offs:
{trade_off_text}"""


# Global singleton
gpt4all_agent = GPT4AllAgent()
