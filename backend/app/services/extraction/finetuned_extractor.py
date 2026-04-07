"""Fine-tuned T5/Llama+LoRA extractor for transcript-to-PCR extraction.

This module loads a fine-tuned model and runs inference to extract
structured PCR fields from transcripts. Requires a trained model checkpoint.

T5 output format: flat string "field: value ; field: value ; ..."
Array fields separated by " | ", medications_given as "Drug 1.5mg IV"
Input prompt must match training: "extract pcr: <transcript>"
"""

import re
import time

from app.schemas.pcr import PCRDocument
from app.services.extraction.base import ExtractionResult, ExtractionService
from app.utils.logging import logger

# Fields the T5 model outputs as plain integers
INT_FIELDS = {
    "age", "bp_systolic", "bp_diastolic", "heart_rate",
    "respiratory_rate", "spo2", "gcs_total", "pain_scale",
    "blood_glucose", "etco2",
}

# Fields the T5 model outputs as float
FLOAT_FIELDS = {"temperature"}

# Fields the T5 model outputs as pipe-separated lists
ARRAY_FIELDS = {
    "allergies", "medications_current", "past_medical_history",
    "procedures", "signs_symptoms",
}

# Regex to parse medication string: "DrugName 1.5mg IV" or "DrugName 324.0mg PO"
_MED_RE = re.compile(r"^(\S+)\s+([\d.]+)([a-zA-Z%]+)\s+(\S+)$")


class FineTunedExtractor(ExtractionService):
    """Fine-tuned T5-base or Llama+LoRA extraction model."""

    def __init__(self, model_path: str, device: str = "cpu"):
        self._model_path = model_path
        self._device = device
        self._model = None
        self._tokenizer = None
        self._loaded = False

    def load_model(self) -> None:
        """Load the fine-tuned model from disk. Deferred to avoid import cost at startup."""
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            logger.info(f"Loading fine-tuned model from {self._model_path}")
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_path)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self._model_path)
            self._model.to(self._device)
            self._model.eval()
            self._loaded = True
            logger.info("Fine-tuned model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load fine-tuned model: {e}")
            raise

    async def extract(self, transcript: str) -> ExtractionResult:
        """Extract PCR fields using the fine-tuned model."""
        if not self._loaded:
            self.load_model()

        start = time.perf_counter()

        # Input prompt must match training format exactly
        input_text = f"extract pcr: {transcript}"
        inputs = self._tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
        ).to(self._device)

        import torch

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_length=1024,
                num_beams=4,
                output_scores=True,
                return_dict_in_generate=True,
            )

        raw_output = self._tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
        latency_ms = (time.perf_counter() - start) * 1000

        # Parse flat string output → dict
        parsed = self._parse_flat_output(raw_output)
        pcr = self._build_pcr(parsed)
        confidence_map = self._compute_confidence(pcr, outputs)

        return ExtractionResult(
            pcr=pcr,
            confidence_map=confidence_map,
            raw_output=raw_output,
            latency_ms=latency_ms,
            model_name=self.model_name,
        )

    @property
    def model_name(self) -> str:
        return "finetuned_t5"

    def _parse_flat_output(self, text: str) -> dict:
        """Parse T5 flat string output into a PCR dict.

        Input format: "field: value ; field: value ; ..."
        Array fields: "allergies: penicillin | sulfa"
        Medications: "medications_given: Aspirin 324.0mg PO | Nitroglycerin 0.4mg SL"
        Null values: "field: null"
        """
        pcr: dict = {}

        for part in text.split(" ; "):
            part = part.strip()
            if ": " not in part:
                continue
            key, val = part.split(": ", 1)
            key = key.strip()
            val = val.strip()

            if val == "null" or val == "":
                pcr[key] = None
            elif key in ARRAY_FIELDS:
                pcr[key] = [v.strip() for v in val.split(" | ") if v.strip()]
            elif key == "medications_given":
                pcr[key] = self._parse_medications(val)
            elif key in INT_FIELDS:
                try:
                    pcr[key] = int(float(val))
                except ValueError:
                    pcr[key] = None
            elif key in FLOAT_FIELDS:
                try:
                    pcr[key] = float(val)
                except ValueError:
                    pcr[key] = None
            else:
                pcr[key] = val

        return pcr

    def _parse_medications(self, val: str) -> list[dict]:
        """Parse medication string back to list of structured dicts.

        Format: "DrugName 1.5mg IV | DrugName2 324.0mg PO"
        Returns: [{"drug": "DrugName", "dose": 1.5, "unit": "mg", "route": "IV"}, ...]
        """
        meds = []
        for med_str in val.split(" | "):
            med_str = med_str.strip()
            if not med_str:
                continue
            m = _MED_RE.match(med_str)
            if m:
                meds.append({
                    "drug": m.group(1),
                    "dose": float(m.group(2)),
                    "unit": m.group(3),
                    "route": m.group(4),
                })
            else:
                # Fallback: store drug name only
                parts = med_str.split()
                meds.append({"drug": parts[0], "dose": None, "unit": None, "route": None})
        return meds if meds else []

    def _build_pcr(self, data: dict) -> PCRDocument:
        """Build PCRDocument from parsed output dict."""
        clean = {}
        for field_name in PCRDocument.model_fields:
            value = data.get(field_name)
            if value is not None:
                clean[field_name] = value
        try:
            return PCRDocument(**clean)
        except Exception as e:
            logger.error(f"Failed to build PCRDocument from fine-tuned output: {e}")
            return PCRDocument()

    def _compute_confidence(self, pcr: PCRDocument, outputs) -> dict[str, float]:
        """Derive per-field confidence from token-level log probabilities."""
        import math

        confidence_map = {}
        pcr_dict = pcr.model_dump()

        avg_logprob = None
        if hasattr(outputs, "scores") and outputs.scores:
            import torch

            logprobs = []
            for i, score in enumerate(outputs.scores):
                token_id = outputs.sequences[0][i + 1]
                log_prob = torch.log_softmax(score[0], dim=-1)[token_id].item()
                logprobs.append(log_prob)
            if logprobs:
                avg_logprob = sum(logprobs) / len(logprobs)

        default_conf = 0.8
        if avg_logprob is not None:
            default_conf = min(1.0, max(0.0, math.exp(avg_logprob)))

        for field_name, value in pcr_dict.items():
            if value is not None and value != [] and value != "":
                confidence_map[field_name] = default_conf

        return confidence_map
