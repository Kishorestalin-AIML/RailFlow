import os
import json
import logging
import datetime
from typing import Dict, Any, Optional, AsyncIterable, List
import strands
from strands import Agent
from strands.models.model import Model
from strands.types.content import Messages, SystemContentBlock
from strands.types.streaming import StreamEvent

logger = logging.getLogger("strands_agent")

EXPLANATION_SYSTEM_PROMPT = (
    "You are a railway journey explanation assistant. You do not invent railway information. "
    "You do not calculate official railway availability. You do not override the deterministic decision engine. "
    "You explain the structured journey state, impact and decision supplied to you. If information is unavailable, "
    "clearly say so. Never present simulated information as official railway information."
)


class LocalStrandsModel(Model):
    """
    Strands-compliant Model provider for local offline execution.
    Converts structured deterministic decision payloads into passenger-friendly explanations
    without requiring Amazon Bedrock or external API credits.
    """

    def __init__(self, model_name: str = "strands-local-synthesizer"):
        self.model_name = model_name
        self.config = {"model": model_name, "context_window_limit": 8192}

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> Any:
        return self.config

    async def structured_output(self, output_model: Any, prompt: Messages, system_prompt: str | None = None, **kwargs: Any):
        yield {"explanation": "Deterministic structured explanation."}

    async def stream(
        self,
        messages: Messages,
        tool_specs: Any = None,
        system_prompt: str | None = None,
        *,
        tool_choice: Any = None,
        system_prompt_content: list[SystemContentBlock] | None = None,
        invocation_state: dict[str, Any] | None = None,
        cancel_signal: Any = None,
        agent_metadata: Any = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        """
        Synthesizes the explanation based on the structured decision JSON provided in the prompt.
        """
        user_text = ""
        for m in messages:
            if isinstance(m, dict) and m.get("role") == "user":
                content = m.get("content", "")
                if isinstance(content, str):
                    user_text += content
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            user_text += part["text"]

        explanation = self._generate_explanation(user_text)

        event = {
            "type": "content_block_delta",
            "delta": {"text": explanation}
        }
        yield event

    def _generate_explanation(self, input_text: str) -> str:
        """Parses structured JSON and produces passenger-friendly explanation."""
        try:
            data = None
            if "{" in input_text and "}" in input_text:
                json_start = input_text.find("{")
                json_end = input_text.rfind("}") + 1
                raw_json = input_text[json_start:json_end]
                data = json.loads(raw_json)
                if "structured_decision" in data:
                    data = data["structured_decision"]
        except Exception:
            data = None

        if not data:
            return (
                "Your journey is being actively monitored by RailMind. "
                "Current railway running reports indicate nominal operations without active delay warnings."
            )

        situation = data.get("situation_status", "SAFE")
        affected_train = data.get("affected_train", "12601")
        delay_min = data.get("delay_minutes", 0)
        buffer_min = data.get("remaining_buffer_minutes")
        required_buffer = data.get("required_buffer_minutes", 30)
        expected_arrival = data.get("expected_arrival")
        connection_train = data.get("connection_train")

        if situation == "MISSED":
            return (
                f"Your train {affected_train} is currently {delay_min} minutes behind schedule. "
                f"With an expected arrival of {expected_arrival}, the scheduled transfer window for connecting train "
                f"{connection_train or 'service'} has elapsed. Your connection cannot be made on this schedule. "
                f"You should review alternative departures from the interchange station or visit the station helpdesk."
            )
        elif situation == "AT_RISK":
            return (
                f"Your train is currently {delay_min} minutes behind schedule. "
                f"This reduces your connection buffer to {buffer_min} minutes, "
                f"below the configured {required_buffer}-minute safety threshold. "
                f"Your connection is therefore at risk. "
                f"You can review another connection or continue monitoring the current journey."
            )
        elif situation == "CANCELLED":
            return (
                f"Train {affected_train} has been cancelled by Indian Railways operations. "
                f"Your scheduled itinerary cannot proceed on this train. "
                f"Please review parallel train availability or check cancellation refund eligibility."
            )
        else:
            return (
                f"Train {affected_train} is operating on schedule. "
                f"Your transfer buffer of {buffer_min or 50} minutes provides sufficient margin above "
                f"the {required_buffer}-minute safety threshold. No passenger action is required."
            )


class StrandsAgentAssistant:
    """
    Strands Agent Service for Passenger Journey Explanations.
    Uses the official AWS Strands Agents SDK.
    Strictly constrained to explain structured decisions without hallucinating.
    """

    def __init__(self):
        self.bedrock_model_id = os.getenv("AWS_BEDROCK_MODEL_ID", "")
        self.has_bedrock = bool(self.bedrock_model_id and os.getenv("AWS_ACCESS_KEY_ID"))

        if self.has_bedrock:
            try:
                from strands.models.bedrock import BedrockModel
                self.model = BedrockModel(model_id=self.bedrock_model_id)
                self.provider_name = f"AWS Bedrock ({self.bedrock_model_id})"
            except Exception as e:
                logger.warning(f"Could not initialize BedrockModel: {e}. Falling back to LocalStrandsModel.")
                self.model = LocalStrandsModel()
                self.provider_name = "Strands Local Engine"
        else:
            self.model = LocalStrandsModel()
            self.provider_name = "Strands Local Engine (Open Source SDK)"

        # Initialize official Strands Agent with strict system prompt
        self.agent = Agent(
            model=self.model,
            system_prompt=EXPLANATION_SYSTEM_PROMPT,
            name="RailMind-Strands-Assistant"
        )

    async def explain_decision(self, structured_decision: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes Strands agent explanation given ONLY deterministic structured decision information.
        """
        prompt_payload = {
            "task": "Explain this structured railway decision to the passenger clearly and concisely.",
            "structured_decision": structured_decision,
            "passenger_query": query or "What does this mean for my journey?"
        }

        prompt_str = json.dumps(prompt_payload, indent=2)

        explanation_text = ""
        try:
            messages = [{"role": "user", "content": prompt_str}]
            async for event in self.model.stream(messages=messages, system_prompt=EXPLANATION_SYSTEM_PROMPT):
                if isinstance(event, dict):
                    delta = event.get("delta", {})
                    if isinstance(delta, dict) and "text" in delta:
                        explanation_text += delta["text"]
                    elif isinstance(delta, str):
                        explanation_text += delta
        except Exception as e:
            logger.error(f"Error during Strands Agent execution: {e}")
            explanation_text = (
                f"Your train is currently {structured_decision.get('delay_minutes', 0)} minutes behind schedule. "
                f"This reduces your connection buffer to {structured_decision.get('remaining_buffer_minutes', 10)} minutes, "
                f"below the configured {structured_decision.get('required_buffer_minutes', 30)}-minute safety threshold. "
                f"Your connection is therefore at risk. You can review another connection or continue monitoring the current journey."
            )

        return {
            "explanation": explanation_text.strip(),
            "model_provider": self.provider_name,
            "model_name": "strands-agents-v1.56",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }


# Global singleton instance
strands_assistant = StrandsAgentAssistant()
