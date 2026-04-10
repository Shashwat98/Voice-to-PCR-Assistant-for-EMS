"""Correction parser — converts natural language corrections to structured intents."""

import json
from typing import Optional

from app.schemas.correction import CorrectionIntent
from app.schemas.pcr import PCRDocument
from app.services.llm.ollama_client import OllamaClient
from app.utils.logging import logger

CORRECTION_SYSTEM_PROMPT = """You are a medical documentation correction parser. Given a natural language correction utterance from a paramedic and the current state of a Patient Care Report (PCR), parse the correction into one or more structured intents.

Each intent should have:
- "field": the PCR field name to modify (one of: age, sex, chief_complaint, primary_impression, secondary_impression, bp_systolic, bp_diastolic, heart_rate, respiratory_rate, spo2, gcs_total, avpu, pain_scale, temperature, blood_glucose, etco2, cardiac_rhythm, allergies, medications_current, past_medical_history, medications_given, procedures, signs_symptoms, events_leading, narrative_text)
- "action": one of "update" (replace value), "append" (add to list), "remove" (remove from list), "clear" (set to null/empty)
- "value": the new value to set/add/remove
- "confidence": 0.0-1.0, how confident you are in parsing this correction

Return a JSON object with key "intents" containing an array of intent objects. If the utterance is unclear, return {"intents": []}.

Examples:
- "Change heart rate to 108" -> {"intents": [{"field": "heart_rate", "action": "update", "value": 108, "confidence": 0.95}]}
- "Add sulfa to allergies" -> {"intents": [{"field": "allergies", "action": "append", "value": "sulfa", "confidence": 0.9}]}
- "BP is 120 over 80" -> {"intents": [{"field": "bp_systolic", "action": "update", "value": 120, "confidence": 0.9}, {"field": "bp_diastolic", "action": "update", "value": 80, "confidence": 0.9}]}

Return ONLY the JSON object."""


class CorrectionParser:
    """Parse natural language corrections into structured field updates."""

    def __init__(self, ollama_client: OllamaClient):
        self._ollama_client = ollama_client

    async def parse(
        self, utterance: str, current_pcr: Optional[PCRDocument] = None
    ) -> list[CorrectionIntent]:
        """Parse a correction utterance into structured intents."""
        context = ""
        if current_pcr:
            pcr_dict = current_pcr.model_dump(exclude_none=True)
            populated = {k: v for k, v in pcr_dict.items() if v and v != []}
            context = f"\n\nCurrent PCR state:\n{json.dumps(populated, indent=2, default=str)}"

        user_message = f'Correction utterance: "{utterance}"{context}'

        raw = await self._ollama_client.chat_completion(
            system_prompt=CORRECTION_SYSTEM_PROMPT,
            user_message=user_message,
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                intents_data = parsed.get("intents", parsed.get("corrections", []))
            elif isinstance(parsed, list):
                intents_data = parsed
            else:
                intents_data = []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse correction response: {raw[:200]}")
            return []

        intents = []
        for item in intents_data:
            try:
                intents.append(CorrectionIntent(**item))
            except Exception as e:
                logger.warning(f"Invalid correction intent: {item}, error: {e}")

        return intents