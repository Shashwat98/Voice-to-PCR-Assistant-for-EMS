"""Gap completion — recover missed transcript values + deterministic transforms."""

import json
import re

from fastapi import APIRouter, HTTPException

from app.dependencies import get_gap_detector, get_ollama_client, get_session_manager
from app.schemas.gap_completion import GapCompletionRequest, GapCompletionResponse, FieldSuggestion
from app.utils.logging import logger

router = APIRouter(prefix="/sessions/{session_id}", tags=["gap_completion"])

# Deterministic rules: no LLM needed

AVPU_RULES = [
    (r"\b(alert and oriented|a&o|a & o|aox\d|a&o\s*x\s*\d|fully alert|patient is alert|alert)\b", "Alert"),
    (r"\b(responds? to voice|verbal stimuli|responsive to voice)\b", "Verbal"),
    (r"\b(responds? to pain|pain stimuli|responsive to pain)\b", "Pain"),
    (r"\b(unresponsive|no response|not responsive)\b", "Unresponsive"),
]

ALLERGY_RULES = [
    (r"\b(no known allergies|nkda|no known drug allergies|no allergies|denies allergies)\b", ["NKDA"]),
]


def apply_deterministic_rules(transcript: str, populated_fields: dict) -> list[FieldSuggestion]:
    """Apply safe, hardcoded mappings before invoking LLM."""
    suggestions = []
    text = transcript.lower()

    # AVPU
    if "avpu" not in populated_fields or populated_fields.get("avpu") is None:
        for pattern, value in AVPU_RULES:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                suggestions.append(FieldSuggestion(
                    field="avpu",
                    value=value,
                    confidence="medium",
                    reason=f"Deterministic transform: transcript contains '{match.group()}'",
                ))
                break

    # Allergies
    if "allergies" not in populated_fields or populated_fields.get("allergies") in (None, []):
        for pattern, value in ALLERGY_RULES:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                suggestions.append(FieldSuggestion(
                    field="allergies",
                    value=value,
                    confidence="high",
                    reason=f"Explicit: transcript states '{match.group()}'",
                ))
                break

    return suggestions


# LLM prompt for recovering explicit values missed by T5

COMPLETION_SYSTEM_PROMPT = """You are a medical documentation assistant helping recover missed values in a Patient Care Report (PCR).

You are given:
1. the current PCR state
2. the original transcript

Your job is NOT to guess missing clinical data.
Your job is ONLY to suggest fields that can be filled because the information was explicitly stated in the transcript.

STRICT RULES
1. ONLY suggest a value if it is explicitly stated in the transcript.
2. NEVER guess, estimate, or fabricate any value.
3. NEVER use typical values, priors, or clinical assumptions.
4. NEVER infer vital signs, medication doses, numerical values, or scores unless explicitly stated.
5. NEVER infer clinical values that require medical judgment.
6. NEVER suggest a value for a field already populated in the current PCR state.
7. NEVER infer GCS from alertness, orientation, or speech.
8. NEVER infer medications from diagnosis or protocol.
9. NEVER infer past medical history from age or presentation.
10. NEVER infer impression from treatment given.
11. For fields with insufficient evidence, omit them entirely.
12. If nothing can be safely recovered, return {"suggestions": []}.

ALLOWED EVIDENCE: EXPLICIT ONLY
The value must be directly stated in the transcript.
Examples:
- "SpO2 94% on room air" -> spo2 = 94
- "GCS 15" -> gcs_total = 15
- "pain is 7 out of 10" -> pain_scale = 7
- "history of hypertension and diabetes" -> past_medical_history = ["Hypertension", "Diabetes"]
- "gave aspirin 324 milligrams orally" -> medications_given = [{"drug": "Aspirin", "dose": 324, "unit": "mg", "route": "PO"}]

DISALLOWED INFERENCE (DO NOT DO ANY OF THESE)
- Guess SpO2, BP, HR, RR, pain score, or GCS
- Infer GCS = 15 from "alert," "talking," or "oriented"
- Infer medications from diagnosis or protocol
- Infer PMH from age or presentation
- Infer impression from treatment
- Fill values from norms, dataset patterns, or clinical expectations
- Infer incident location from vague context

CONFIDENCE
- "high" = directly stated in the transcript word for word
- Never output low or medium confidence suggestions

REASON
For each suggestion, quote the exact transcript phrase supporting the value.

OUTPUT FORMAT
{"suggestions": [{"field": "field_name", "value": <value>, "confidence": "high", "reason": "exact quote from transcript"}]}

If nothing can be safely filled: {"suggestions": []}"""


@router.post("/complete-gaps", response_model=GapCompletionResponse)
async def complete_gaps(session_id: str, request: GapCompletionRequest):
    """Recover missed transcript values using deterministic rules + LLM."""
    session_mgr = get_session_manager()
    session = await session_mgr.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    pcr_state = session.pcr_manager.get_state()
    detector = get_gap_detector()
    gaps = detector.detect_gaps(pcr_state)

    if gaps.total_gaps == 0:
        return GapCompletionResponse(suggestions=[], message="All fields are complete.")

    pcr_dict = pcr_state.pcr.model_dump(exclude_none=True)
    populated = {k: v for k, v in pcr_dict.items() if v and v != []}

    all_suggestions: list[FieldSuggestion] = []

    # Phase 1: deterministic rules (no LLM, no hallucination risk)
    if request.transcript:
        deterministic = apply_deterministic_rules(request.transcript, populated)
        all_suggestions.extend(deterministic)

    # Track fields already handled by deterministic rules
    determined_fields = {s.field for s in all_suggestions}

    # Phase 2: LLM for remaining missed explicit values
    remaining_gaps = [
        g for g in gaps.missing_mandatory + gaps.missing_required + gaps.missing_recommended
        if g.field_name not in determined_fields and g.field_name not in populated
    ]

    if remaining_gaps and request.transcript:
        missing_list = "\n".join(f"- {g.field_name}: {g.description}" for g in remaining_gaps)

        user_message = f"""Current PCR state:
{json.dumps(populated, indent=2, default=str)}

Missing fields to check:
{missing_list}

Original transcript:
{request.transcript}

Identify any missing field values that are EXPLICITLY stated in the transcript but were missed by the extraction model."""

        ollama = get_ollama_client()
        try:
            raw = await ollama.chat_completion(
                system_prompt=COMPLETION_SYSTEM_PROMPT,
                user_message=user_message,
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            parsed = json.loads(raw)
            for item in parsed.get("suggestions", []):
                try:
                    field = item["field"]
                    # Skip if already populated or already suggested by deterministic rules
                    if field in populated or field in determined_fields:
                        continue
                    # Only accept high confidence from LLM
                    if item.get("confidence") != "high":
                        continue
                    all_suggestions.append(FieldSuggestion(
                        field=field,
                        value=item["value"],
                        confidence="high",
                        reason=item.get("reason", ""),
                    ))
                except Exception as e:
                    logger.warning(f"Invalid LLM suggestion: {item}, error: {e}")

        except Exception as e:
            logger.error(f"LLM gap completion failed: {e}")

    return GapCompletionResponse(
        suggestions=all_suggestions,
        message=f"Recovered {len(all_suggestions)} fields ({len([s for s in all_suggestions if s.confidence == 'high'])} explicit, {len([s for s in all_suggestions if s.confidence == 'medium'])} deterministic).",
    )